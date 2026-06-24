from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class NodeKind(StrEnum):
    START = "start"
    FIND_IMAGE = "find_image"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    DELAY = "delay"
    STOP = "stop"


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
            id=raw["id"],
            kind=NodeKind(raw["kind"]),
            title=raw["title"],
            x=float(raw.get("x", 0)),
            y=float(raw.get("y", 0)),
            config=dict(raw.get("config", {})),
        )


@dataclass(slots=True)
class Edge:
    source: str
    target: str
    label: str = "next"


@dataclass(slots=True)
class Workflow:
    name: str = "Untitled workflow"
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    version: int = 1

    def validate(self) -> list[str]:
        errors: list[str] = []
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("Node IDs must be unique.")
        starts = [node for node in self.nodes if node.kind == NodeKind.START]
        if len(starts) != 1:
            errors.append("A workflow must contain exactly one Start node.")
        known = set(ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                errors.append("Every edge must reference existing nodes.")
        return errors

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Workflow":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=raw.get("name", "Untitled workflow"),
            version=int(raw.get("version", 1)),
            nodes=[Node.from_dict(node) for node in raw.get("nodes", [])],
            edges=[Edge(**edge) for edge in raw.get("edges", [])],
        )

