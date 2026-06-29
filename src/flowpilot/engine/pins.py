"""Node pin layout — the shared contract between the editor and the runner.

Mirrors `NODE_SPECS` in web/src/types.ts. Each node declares its input pins
(left side) and output pins (right side). Exec pins (kind "exec") carry control
flow; data pins (kind "bool"/"string"/"point"/"var") carry typed values. The
runner uses the exec outputs to decide where flow goes next, and the data pins
to know which inputs to resolve.
"""

from __future__ import annotations

from dataclasses import dataclass

from flowpilot.engine.model import NodeKind

# Pin kinds → wire colour. "var" is a placeholder whose real type comes from the
# task variable a var_get/var_set node points at (the editor colours it then).
PIN_COLORS = {
    "exec": "#e2e8f0",
    "bool": "#ef4444",
    "string": "#ec4899",
    "point": "#3b82f6",
    "var": "#94a3b8",
}


@dataclass(frozen=True, slots=True)
class Pin:
    id: str
    dir: str    # "in" | "out"
    kind: str   # "exec" | "bool" | "string" | "point" | "var"
    label: str


def _i(kind: str = "exec", id: str = "exec", label: str = "") -> Pin:
    return Pin(id=id, dir="in", kind=kind, label=label)


def _o(id: str, label: str, kind: str = "exec") -> Pin:
    return Pin(id=id, dir="out", kind=kind, label=label)


NODE_PINS: dict[NodeKind, list[Pin]] = {
    NodeKind.START: [_o("then", "")],
    NodeKind.STOP: [_i()],
    NodeKind.FIND_CLICK: [
        _i(),
        _o("success", "成功"),
        _o("fail", "失败"),
        _o("found", "找到", "bool"),
    ],
    NodeKind.FIND_TYPE: [
        _i(),
        _i("string", "text", "文本"),
        _o("success", "成功"),
        _o("fail", "失败"),
        _o("found", "找到", "bool"),
    ],
    NodeKind.TYPE_TEXT: [_i(), _i("string", "text", "文本"), _o("then", "完成")],
    NodeKind.KEY_PRESS: [_i(), _o("then", "完成")],
    NodeKind.DELAY: [_i(), _o("then", "完成")],
    NodeKind.LAUNCH_APP: [_i(), _o("then", "完成")],
    NodeKind.CONDITION: [
        _i(),
        _o("true", "真"),
        _o("false", "假"),
        _o("found", "找到", "bool"),
    ],
    NodeKind.BRANCH: [_i(), _i("bool", "cond", "条件"), _o("true", "真"), _o("false", "假")],
    NodeKind.LOOP: [_i(), _o("body", "循环体"), _o("done", "完成")],
    NodeKind.LOOP_WHILE: [
        _i(),
        _i("bool", "cond", "条件"),
        _o("body", "循环体"),
        _o("done", "完成"),
    ],
    NodeKind.SWIPE: [_i(), _o("success", "成功"), _o("fail", "失败")],
    NodeKind.VAR_GET: [_o("value", "值", "var")],
    NodeKind.VAR_SET: [_i(), _i("var", "value", "值"), _o("then", "完成")],
}


def exec_outputs(kind: NodeKind) -> list[str]:
    """Ordered exec output handle ids for a node kind."""
    return [p.id for p in NODE_PINS.get(kind, []) if p.dir == "out" and p.kind == "exec"]


def default_exec_out(kind: NodeKind) -> str | None:
    """The exec output to follow for plain (non-branching) nodes."""
    outs = exec_outputs(kind)
    return outs[0] if outs else None
