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
    CONDITION = "condition"        # branch on whether a template is on screen
    LOOP = "loop"                  # repeat the body a fixed number of times
    LOOP_WHILE = "loop_while"      # repeat the body while a condition holds
    SET_VAR = "set_var"            # write a named boolean variable
    CHECK_VAR = "check_var"        # branch on a named boolean variable
    STOP = "stop"


# Node kinds that branch to two labelled edges instead of a single "next".
# CONDITION / CHECK_VAR use "true"/"false"; loops use "body"/"done".
BRANCHING = {NodeKind.CONDITION, NodeKind.CHECK_VAR, NodeKind.LOOP, NodeKind.LOOP_WHILE}


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
        return cls(
            id=str(raw.get("id") or uuid4().hex),
            kind=NodeKind(raw["kind"]),
            title=str(raw.get("title", "")),
            x=float(raw.get("x", 0)),
            y=float(raw.get("y", 0)),
            config=dict(raw.get("config", {})),
        )


@dataclass(slots=True)
class Edge:
    source: str
    target: str
    label: str = "next"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Edge":
        return cls(
            source=str(raw["source"]),
            target=str(raw["target"]),
            label=str(raw.get("label", "next")),
        )


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

    def node_by_id(self, node_id: str) -> Node:
        try:
            return next(n for n in self.nodes if n.id == node_id)
        except StopIteration as exc:
            raise KeyError(node_id) from exc

    def start_node(self) -> Node | None:
        return next((n for n in self.nodes if n.kind == NodeKind.START), None)

    def outgoing(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        return cls(
            id=str(raw.get("id") or uuid4().hex),
            name=str(raw.get("name", "New task")),
            hotkey=str(raw.get("hotkey", "")),
            stop_hotkey=str(raw.get("stop_hotkey", "")),
            trigger_mode=TriggerMode(raw.get("trigger_mode", "once")),
            repeat=max(1, int(raw.get("repeat", 1))),
            enabled=bool(raw.get("enabled", True)),
            nodes=[Node.from_dict(n) for n in raw.get("nodes", [])],
            edges=[Edge.from_dict(e) for e in raw.get("edges", [])],
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
