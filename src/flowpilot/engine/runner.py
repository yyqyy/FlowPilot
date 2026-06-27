from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from flowpilot.engine.actions import InputController, decode_template
from flowpilot.engine.model import (
    NodeKind,
    Task,
    TriggerMode,
    Variable,
    _var_default,
)
from flowpilot.engine.pins import default_exec_out
from flowpilot.screen import MatchResult


class Locator:
    """Anything that can find a template on screen (ScreenMatcher or a fake)."""

    def locate(self, template, *, threshold: float) -> MatchResult | None:  # pragma: no cover
        raise NotImplementedError


LogSink = Callable[[str], None]


def _int(config: dict, key: str, default: int) -> int:
    try:
        return int(float(config.get(key, default)))
    except (TypeError, ValueError):
        return default


def _float(config: dict, key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on", "是")
    return bool(value)


def _coerce(value: Any, var_type: str) -> Any:
    if var_type == "bool":
        return _as_bool(value)
    if var_type == "string":
        return "" if value is None else str(value)
    if var_type == "point":
        if isinstance(value, dict):
            return {"x": _int(value, "x", 0), "y": _int(value, "y", 0)}
        return {"x": 0, "y": 0}
    return value


# Default "wait after this node runs" per kind. Screen-affecting actions pause 1s
# so the UI can react before the next find/click; control-flow nodes don't wait.
# Read from node.config["post_delay"] when present, so each node can override it.
_POST_DELAY_DEFAULT: dict[NodeKind, float] = {
    NodeKind.FIND_CLICK: 1.0,
    NodeKind.FIND_TYPE: 1.0,
    NodeKind.TYPE_TEXT: 1.0,
    NodeKind.KEY_PRESS: 1.0,
    NodeKind.SWIPE: 1.0,
}


def _post_delay(node) -> float:
    return _float(node.config, "post_delay", _POST_DELAY_DEFAULT.get(node.kind, 0.0))


@dataclass
class RunContext:
    controller: InputController
    locator: Locator
    stop: threading.Event
    log: LogSink
    task: Task
    last_match: MatchResult | None = field(default=None)
    vars: dict[str, Any] = field(default_factory=dict)
    var_by_name: dict[str, Variable] = field(default_factory=dict)
    loop_counters: dict[str, int] = field(default_factory=dict)
    # Outputs produced by impure nodes (find_click 找到 etc.), keyed by (node, pin).
    pin_values: dict[tuple[str, str], Any] = field(default_factory=dict)


def interruptible_sleep(seconds: float, stop: threading.Event) -> None:
    deadline = time.monotonic() + max(0.0, seconds)
    while not stop.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.05, remaining))


def _locate_config(node, ctx: RunContext) -> MatchResult | None:
    template = decode_template(str(node.config.get("templateData", "")))
    if template is None:
        ctx.log(f"[{node.kind}] {node.title}: 没有可用的模板图片")
        return None
    threshold = _float(node.config, "threshold", 0.85)
    return ctx.locator.locate(template, threshold=threshold)


def _resolve_input(ctx: RunContext, node_id: str, handle: str, default: Any = None) -> Any:
    """Read the value feeding a node's data input pin.

    Pulls live from a var_get source; otherwise reads the value a producing node
    pushed into pin_values. Returns `default` when nothing is wired/available."""
    edge = ctx.task.data_into(node_id, handle)
    if edge is None:
        return default
    try:
        source = ctx.task.node_by_id(edge.source)
    except KeyError:
        return default
    if source.kind == NodeKind.VAR_GET:
        name = str(source.config.get("name", "")).strip()
        var = ctx.var_by_name.get(name)
        fallback = var.default if var else default
        return ctx.vars.get(name, fallback)
    return ctx.pin_values.get((edge.source, edge.source_handle), default)


def _execute(node, ctx: RunContext) -> str | None:
    """Run one node. Returns the exec output handle to follow, or None to stop."""
    ctx.log(f"[{node.kind}] {node.title}")

    if node.kind == NodeKind.START:
        return "then"
    if node.kind == NodeKind.STOP:
        return None
    if node.kind == NodeKind.VAR_GET:
        return None  # pure data node, never reached via exec flow

    if node.kind == NodeKind.DELAY:
        low = _float(node.config, "min_seconds", 0.5)
        high = _float(node.config, "max_seconds", low)
        delay = random.uniform(min(low, high), max(low, high))
        ctx.log(f"  等待 {delay:.2f}s")
        interruptible_sleep(delay, ctx.stop)
        return "then"

    if node.kind == NodeKind.FIND_CLICK:
        match = _locate_config(node, ctx)
        ctx.pin_values[(node.id, "found")] = match is not None
        if match is None:
            ctx.log("  未找到图片 → 失败")
            return "fail"
        ctx.last_match = match
        x = match.center[0] + _int(node.config, "offsetX", 0)
        y = match.center[1] + _int(node.config, "offsetY", 0)
        button = str(node.config.get("button", "left"))
        clicks = 2 if button == "double" else 1
        ctx.log(f"  在 ({x}, {y}) 点击 ({match.confidence:.0%})")
        ctx.controller.click(x, y, button="left" if button == "double" else button, clicks=clicks)
        return "success"

    if node.kind == NodeKind.FIND_TYPE:
        text = str(_resolve_input(ctx, node.id, "text", node.config.get("text", "")))
        has_template = bool(str(node.config.get("templateData", "")).strip())
        if has_template:
            match = _locate_config(node, ctx)
            ctx.pin_values[(node.id, "found")] = match is not None
            if match is None:
                ctx.log("  未找到输入位置 → 失败")
                return "fail"
            ctx.last_match = match
            ctx.controller.click(match.center[0], match.center[1])
        else:
            ctx.pin_values[(node.id, "found")] = True
        ctx.log(f"  输入 {len(text)} 个字符")
        ctx.controller.type_text(text)
        return "success"

    if node.kind == NodeKind.TYPE_TEXT:
        text = str(_resolve_input(ctx, node.id, "text", node.config.get("text", "")))
        ctx.controller.type_text(text)
        return "then"

    if node.kind == NodeKind.KEY_PRESS:
        combo = str(node.config.get("keys", ""))
        if combo:
            ctx.log(f"  按键 {combo}")
            ctx.controller.press(combo)
        return "then"

    if node.kind == NodeKind.LAUNCH_APP:
        path = str(node.config.get("path", ""))
        args = str(node.config.get("args", ""))
        wait = _float(node.config, "wait_seconds", 0.0)
        ctx.log(f"  启动 {path}")
        ctx.controller.launch(path, args, wait)
        if wait > 0:
            interruptible_sleep(wait, ctx.stop)
        return "then"

    if node.kind == NodeKind.SWIPE:
        return _do_swipe(node, ctx)

    if node.kind == NodeKind.CONDITION:
        found = _locate_config(node, ctx) is not None
        ctx.pin_values[(node.id, "found")] = found
        ctx.log(f"  判断：{'找到' if found else '未找到'}")
        return "true" if found else "false"

    if node.kind == NodeKind.BRANCH:
        value = _as_bool(_resolve_input(ctx, node.id, "cond", False))
        ctx.log(f"  分支：{value}")
        return "true" if value else "false"

    if node.kind == NodeKind.VAR_SET:
        name = str(node.config.get("name", "")).strip()
        var = ctx.var_by_name.get(name)
        var_type = var.type if var else "bool"
        if ctx.task.data_into(node.id, "value") is not None:
            value = _resolve_input(ctx, node.id, "value", _var_default(var_type))
        else:
            value = _coerce(node.config.get("value"), var_type)
        if name:
            ctx.vars[name] = value
            ctx.log(f"  设置变量 {name} = {value}")
        return "then"

    if node.kind == NodeKind.LOOP:
        count = _int(node.config, "count", 1)
        seen = ctx.loop_counters.get(node.id, 0)
        if seen < count:
            ctx.loop_counters[node.id] = seen + 1
            ctx.log(f"  循环 {seen + 1}/{count}")
            return "body"
        ctx.loop_counters[node.id] = 0
        return "done"

    if node.kind == NodeKind.LOOP_WHILE:
        max_it = _int(node.config, "max_iterations", 1000)
        seen = ctx.loop_counters.get(node.id, 0)
        if seen < max_it and _loop_condition_met(node, ctx):
            ctx.loop_counters[node.id] = seen + 1
            ctx.log(f"  条件循环 第 {seen + 1} 次")
            return "body"
        ctx.loop_counters[node.id] = 0
        if seen >= max_it:
            ctx.log("  达到最大循环次数")
        return "done"

    return default_exec_out(node.kind)


def _do_swipe(node, ctx: RunContext) -> str:
    raw_points = node.config.get("points", []) or []
    points = [(_float(p, "x", 0.0), _float(p, "y", 0.0)) for p in raw_points]
    if len(points) < 2:
        ctx.log("  滑动点不足（至少 2 个），跳过")
        return "then"
    shot_w = _float(node.config, "shotW", 0.0)
    shot_h = _float(node.config, "shotH", 0.0)
    screen_w, screen_h = ctx.controller.screen_size()
    scale_x = screen_w / shot_w if shot_w else 1.0
    scale_y = screen_h / shot_h if shot_h else 1.0
    real = [(round(x * scale_x), round(y * scale_y)) for x, y in points]
    durations = [_safe_float(d) for d in node.config.get("durations", []) or []]
    button = str(node.config.get("button", "left"))
    ctx.log(f"  滑动 {len(real)} 个点：{real}")
    ctx.controller.drag_path(real, durations, button=button)
    return "then"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.3


def _loop_condition_met(node, ctx: RunContext) -> bool:
    """Whether a loop_while should keep going. Prefer a wired bool input; fall
    back to the image/threshold config when nothing is connected."""
    if ctx.task.data_into(node.id, "cond") is not None:
        return _as_bool(_resolve_input(ctx, node.id, "cond", False))
    if str(node.config.get("source", "image")) == "variable":
        value = _as_bool(ctx.vars.get(str(node.config.get("varName", "")), False))
    else:
        value = _locate_config(node, ctx) is not None
    mode = str(node.config.get("mode", "true"))
    return value if mode == "true" else not value


def _walk(task: Task, ctx: RunContext) -> None:
    current = task.start_node()
    if current is None:
        ctx.log("没有 Start 节点，无法运行")
        return
    ctx.loop_counters.clear()
    ctx.pin_values.clear()
    steps = 0
    while current is not None and not ctx.stop.is_set():
        steps += 1
        if steps > 100_000:
            ctx.log("达到步数上限，停止")
            return
        handle = _execute(current, ctx)
        if handle is None:
            return
        delay = _post_delay(current)
        if delay > 0:
            interruptible_sleep(delay, ctx.stop)
            if ctx.stop.is_set():
                return
        edge = task.exec_out(current.id, handle)
        if edge is None:
            return
        try:
            current = task.node_by_id(edge.target)
        except KeyError:
            ctx.log("连线指向了不存在的节点，停止")
            return


def run_task(
    task: Task,
    *,
    controller: InputController,
    locator: Locator,
    stop: threading.Event,
    log: LogSink = print,
) -> str:
    """Execute a task honoring its trigger mode. Returns a final status string."""
    var_by_name = {v.name: v for v in task.variables if v.name}
    initial_vars = {name: var.default for name, var in var_by_name.items()}
    ctx = RunContext(
        controller=controller,
        locator=locator,
        stop=stop,
        log=log,
        task=task,
        vars=initial_vars,
        var_by_name=var_by_name,
    )

    if task.trigger_mode == TriggerMode.LOOP:
        loops = 0
        while not stop.is_set():
            loops += 1
            ctx.log(f"—— 第 {loops} 次循环 ——")
            _walk(task, ctx)
    else:
        total = task.repeat if task.trigger_mode == TriggerMode.TIMES else 1
        for index in range(max(1, total)):
            if stop.is_set():
                break
            if total > 1:
                ctx.log(f"—— 第 {index + 1}/{total} 次 ——")
            _walk(task, ctx)

    if stop.is_set():
        ctx.log("已停止")
        return "stopped"
    ctx.log("运行完成")
    return "completed"
