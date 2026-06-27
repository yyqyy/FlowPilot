from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class NodeKind(StrEnum):
    START = "start"
    FIND_CLICK = "find_click"      # locate a template, click its center
    FIND_TYPE = "find_type"        # locate a template, click it, then type
    TYPE_TEXT = "type_text"        # type into whatever is focused
    KEY_PRESS = "key_press"        # press a key / combo (e.g. ctrl+c)
    DELAY = "delay"                # fixed or random wait
    LAUNCH_APP = "launch_app"      # start a program, optionally wait
    CONDITION = "condition"        # look for a template, branch 真/假, expose 找到
    BRANCH = "branch"              # UE5 Branch: bool data in → 真/假 exec out
    LOOP = "loop"                  # repeat the body a fixed number of times
    LOOP_WHILE = "loop_while"      # repeat the body while a condition holds
    SWIPE = "swipe"               # press-drag along ordered points on a screenshot
    VAR_GET = "var_get"            # pure node: output a variable's value (data only)
    VAR_SET = "var_set"            # write a value into a named variable
    STOP = "stop"


# Old node kinds that map onto the new model when loading saved tasks.
_LEGACY_KINDS = {"set_var": NodeKind.VAR_SET, "check_var": NodeKind.BRANCH}

# Variable value types. Mirrors web/src/types.ts VariableType.
VAR_TYPES = ("bool", "string", "point")


def _var_default(var_type: str) -> Any:
    if var_type == "string":
        return ""
    if var_type == "point":
        return {"x": 0, "y": 0}
    return False


@dataclass(slots=True)
class Variable:
    name: str
    type: str = "bool"            # one of VAR_TYPES
    default: Any = None
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        if self.type not in VAR_TYPES:
            self.type = "bool"
        if self.default is None:
            self.default = _var_default(self.type)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Variable":
        return cls(
            id=str(raw.get("id") or uuid4().hex),
            name=str(raw.get("name", "")),
            type=str(raw.get("type", "bool")),
            default=raw.get("default"),
        )


@dataclass(slots=True)
class Node:
    kind: NodeKind
    title: str
    x: float = 0
    y: float = 0
    config: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Node":
        raw_kind = str(raw["kind"])
        kind = _LEGACY_KINDS.get(raw_kind, None) or NodeKind(raw_kind)
        return cls(
            id=str(raw.get("id") or uuid4().hex),
            kind=kind,
            title=str(raw.get("title", "")),
            x=float(raw.get("x", 0)),
            y=float(raw.get("y", 0)),
            config=dict(raw.get("config", {})),
        )


@dataclass(slots=True)
class Edge:
    """A wire between two pins. `kind` is "exec" (control flow) or "data"."""

    source: str
    source_handle: str = "then"
    target: str = ""
    target_handle: str = "exec"
    kind: str = "exec"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Edge":
        return cls(
            source=str(raw["source"]),
            source_handle=str(raw.get("source_handle") or raw.get("sourceHandle") or "then"),
            target=str(raw["target"]),
            target_handle=str(raw.get("target_handle") or raw.get("targetHandle") or "exec"),
            kind=str(raw.get("kind", "exec")),
        )


def _legacy_handle(kind: NodeKind | None, label: str) -> str:
    """Map an old single-label edge onto a new exec source-handle id."""
    if label in ("true", "false", "body", "done"):
        return label
    if label in ("", "next"):
        return "success" if kind in (NodeKind.FIND_CLICK, NodeKind.FIND_TYPE) else "then"
    return label


def _migrate_edge(raw: dict[str, Any], kind_by_id: dict[str, NodeKind]) -> Edge:
    source = str(raw["source"])
    return Edge(
        source=source,
        source_handle=_legacy_handle(kind_by_id.get(source), str(raw.get("label", "next"))),
        target=str(raw["target"]),
        target_handle="exec",
        kind="exec",
    )


def _is_new_edge(raw: dict[str, Any]) -> bool:
    return any(k in raw for k in ("source_handle", "sourceHandle", "kind"))


def _ensure_migrated_vars(nodes: list[Node], variables: list[Variable]) -> None:
    """Old set_var/check_var carried a variable name in config; surface those as
    declared variables so the panel shows them after migration."""
    known = {v.name for v in variables if v.name}
    for node in nodes:
        if node.kind in (NodeKind.VAR_SET, NodeKind.BRANCH):
            name = str(node.config.get("name", "")).strip()
            if name and name not in known:
                variables.append(Variable(name=name, type="bool"))
                known.add(name)


class TriggerMode(StrEnum):
    ONCE = "once"     # run the graph one time
    TIMES = "times"   # run the graph `repeat` times
    LOOP = "loop"     # run the graph over and over until stopped


@dataclass(slots=True)
class Task:
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = "New task"
    hotkey: str = ""              # start/restart trigger, e.g. "ctrl+alt+1"
    stop_hotkey: str = ""         # halt-this-task trigger
    trigger_mode: TriggerMode = TriggerMode.ONCE
    repeat: int = 1               # iterations when trigger_mode == TIMES
    enabled: bool = True          # whether the hotkeys are actively listened for
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)

    def node_by_id(self, node_id: str) -> Node:
        try:
            return next(n for n in self.nodes if n.id == node_id)
        except StopIteration as exc:
            raise KeyError(node_id) from exc

    def start_node(self) -> Node | None:
        return next((n for n in self.nodes if n.kind == NodeKind.START), None)

    def exec_out(self, node_id: str, handle: str) -> Edge | None:
        """The exec wire leaving a node from a given source handle, if any."""
        return next(
            (
                e
                for e in self.edges
                if e.kind == "exec" and e.source == node_id and e.source_handle == handle
            ),
            None,
        )

    def data_into(self, node_id: str, handle: str) -> Edge | None:
        """The data wire feeding a node's input handle, if any."""
        return next(
            (
                e
                for e in self.edges
                if e.kind == "data" and e.target == node_id and e.target_handle == handle
            ),
            None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        nodes = [Node.from_dict(n) for n in raw.get("nodes", [])]
        kind_by_id = {n.id: n.kind for n in nodes}
        variables = [Variable.from_dict(v) for v in raw.get("variables", [])]
        edges = [
            Edge.from_dict(e) if _is_new_edge(e) else _migrate_edge(e, kind_by_id)
            for e in raw.get("edges", [])
        ]
        _ensure_migrated_vars(nodes, variables)
        return cls(
            id=str(raw.get("id") or uuid4().hex),
            name=str(raw.get("name", "New task")),
            hotkey=str(raw.get("hotkey", "")),
            stop_hotkey=str(raw.get("stop_hotkey", "")),
            trigger_mode=TriggerMode(raw.get("trigger_mode", "once")),
            repeat=max(1, int(raw.get("repeat", 1))),
            enabled=bool(raw.get("enabled", True)),
            nodes=nodes,
            edges=edges,
            variables=variables,
        )


def summarize(task: Task) -> dict[str, Any]:
    """Lightweight view for the task list (no node payloads)."""
    return {
        "id": task.id,
        "name": task.name,
        "hotkey": task.hotkey,
        "stop_hotkey": task.stop_hotkey,
        "trigger_mode": task.trigger_mode.value,
        "repeat": task.repeat,
        "enabled": task.enabled,
        "nodeCount": len(task.nodes),
    }
