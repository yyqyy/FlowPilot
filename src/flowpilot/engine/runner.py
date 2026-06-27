from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from flowpilot.engine.actions import InputController, decode_template
from flowpilot.engine.model import Node, NodeKind, Task, TriggerMode
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


@dataclass
class RunContext:
    controller: InputController
    locator: Locator
    stop: threading.Event
    log: LogSink
    last_match: MatchResult | None = field(default=None)


def interruptible_sleep(seconds: float, stop: threading.Event) -> None:
    deadline = time.monotonic() + max(0.0, seconds)
    while not stop.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.05, remaining))


def _locate_config(node: Node, ctx: RunContext) -> MatchResult | None:
    template = decode_template(str(node.config.get("templateData", "")))
    if template is None:
        ctx.log(f"[{node.kind}] {node.title}: 没有可用的模板图片")
        return None
    threshold = _float(node.config, "threshold", 0.85)
    return ctx.locator.locate(template, threshold=threshold)


def _execute(node: Node, ctx: RunContext) -> tuple[bool, str | None]:
    """Run one node. Returns (stop_run, branch_label)."""
    ctx.log(f"[{node.kind}] {node.title}")

    if node.kind in (NodeKind.START,):
        return False, None
    if node.kind == NodeKind.STOP:
        return True, None

    if node.kind == NodeKind.DELAY:
        low = _float(node.config, "min_seconds", 0.5)
        high = _float(node.config, "max_seconds", low)
        delay = random.uniform(min(low, high), max(low, high))
        ctx.log(f"  等待 {delay:.2f}s")
        interruptible_sleep(delay, ctx.stop)
        return False, None

    if node.kind == NodeKind.FIND_CLICK:
        match = _locate_config(node, ctx)
        if match is None:
            ctx.log("  未找到图片，停止本次运行")
            return True, None
        ctx.last_match = match
        x = match.center[0] + _int(node.config, "offsetX", 0)
        y = match.center[1] + _int(node.config, "offsetY", 0)
        button = str(node.config.get("button", "left"))
        clicks = 2 if button == "double" else 1
        ctx.log(f"  在 ({x}, {y}) 点击 ({match.confidence:.0%})")
        ctx.controller.click(x, y, button="left" if button == "double" else button, clicks=clicks)
        return False, None

    if node.kind == NodeKind.FIND_TYPE:
        text = str(node.config.get("text", ""))
        has_template = bool(str(node.config.get("templateData", "")).strip())
        if has_template:
            match = _locate_config(node, ctx)
            if match is None:
                ctx.log("  未找到输入位置，停止本次运行")
                return True, None
            ctx.last_match = match
            ctx.controller.click(match.center[0], match.center[1])
        ctx.log(f"  输入 {len(text)} 个字符")
        ctx.controller.type_text(text)
        return False, None

    if node.kind == NodeKind.TYPE_TEXT:
        ctx.controller.type_text(str(node.config.get("text", "")))
        return False, None

    if node.kind == NodeKind.KEY_PRESS:
        combo = str(node.config.get("keys", ""))
        if combo:
            ctx.log(f"  按键 {combo}")
            ctx.controller.press(combo)
        return False, None

    if node.kind == NodeKind.LAUNCH_APP:
        path = str(node.config.get("path", ""))
        args = str(node.config.get("args", ""))
        wait = _float(node.config, "wait_seconds", 0.0)
        ctx.log(f"  启动 {path}")
        ctx.controller.launch(path, args, wait)
        if wait > 0:
            interruptible_sleep(wait, ctx.stop)
        return False, None

    if node.kind == NodeKind.CONDITION:
        found = _locate_config(node, ctx) is not None
        ctx.log(f"  判断：{'找到' if found else '未找到'}")
        return False, "true" if found else "false"

    return False, None


def _walk(task: Task, ctx: RunContext) -> None:
    current = task.start_node()
    if current is None:
        ctx.log("没有 Start 节点，无法运行")
        return
    steps = 0
    while current is not None and not ctx.stop.is_set():
        steps += 1
        if steps > 100_000:
            ctx.log("达到步数上限，停止")
            return
        stop_run, branch = _execute(current, ctx)
        if stop_run:
            return
        edges = task.outgoing(current.id)
        if current.kind == NodeKind.CONDITION:
            edge = next((e for e in edges if e.label == branch), None)
            if edge is None:
                edge = next((e for e in edges if e.label == "next"), None)
        else:
            edge = edges[0] if edges else None
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
    ctx = RunContext(controller=controller, locator=locator, stop=stop, log=log)

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
