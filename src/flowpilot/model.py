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

    def node_by_id(self, node_id: str) -> Node:
        try:
            return next(node for node in self.nodes if node.id == node_id)
        except StopIteration as exc:
            raise KeyError(node_id) from exc

    def connect(self, source: str, target: str) -> None:
        if source == target:
            raise ValueError("A node cannot connect to itself.")
        source_node = self.node_by_id(source)
        target_node = self.node_by_id(target)
        if source_node.kind == NodeKind.STOP:
            raise ValueError("A Stop node cannot have an outgoing connection.")
        if target_node.kind == NodeKind.START:
            raise ValueError("A Start node cannot have an incoming connection.")
        self.edges = [edge for edge in self.edges if edge.source != source]
        self.edges.append(Edge(source, target))

    def remove_node(self, node_id: str) -> None:
        self.node_by_id(node_id)
        self.nodes = [node for node in self.nodes if node.id != node_id]
        self.edges = [
            edge for edge in self.edges if edge.source != node_id and edge.target != node_id
        ]

    def remove_edge(self, source: str, target: str) -> None:
        self.edges = [
            edge for edge in self.edges if not (edge.source == source and edge.target == target)
        ]

    def validate(self) -> list[str]:
        errors: list[str] = []
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("Node IDs must be unique.")
        starts = [node for node in self.nodes if node.kind == NodeKind.START]
        if len(starts) != 1:
            errors.append("A workflow must contain exactly one Start node.")
        known = set(ids)
        outgoing: dict[str, int] = {}
        seen_edges: set[tuple[str, str, str]] = set()
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                errors.append("Every edge must reference existing nodes.")
                continue
            if edge.source == edge.target:
                errors.append("A node cannot connect to itself.")
            key = (edge.source, edge.target, edge.label)
            if key in seen_edges:
                errors.append("Duplicate connections are not allowed.")
            seen_edges.add(key)
            outgoing[edge.source] = outgoing.get(edge.source, 0) + 1
        if any(count > 1 for count in outgoing.values()):
            errors.append("Only one outgoing connection per node is supported.")
        for node in self.nodes:
            errors.extend(self._config_errors(node))
        return errors

    @staticmethod
    def _config_errors(node: Node) -> list[str]:
        prefix = node.title or node.kind.value
        if node.kind == NodeKind.FIND_IMAGE:
            if not str(node.config.get("template", "")).strip():
                return [f"{prefix}: choose a template image."]
            try:
                threshold = float(node.config.get("threshold", 0.85))
            except (TypeError, ValueError):
                return [f"{prefix}: confidence must be a number."]
            if not 0 <= threshold <= 1:
                return [f"{prefix}: confidence must be between 0 and 1."]
        if node.kind == NodeKind.CLICK:
            target = node.config.get("target", "fixed")
            if target not in {"fixed", "last_match"}:
                return [f"{prefix}: unknown click target."]
            if target == "fixed":
                try:
                    int(node.config.get("x", 0))
                    int(node.config.get("y", 0))
                except (TypeError, ValueError):
                    return [f"{prefix}: X and Y must be whole numbers."]
        if node.kind == NodeKind.DELAY:
            try:
                minimum = float(node.config.get("min_seconds", 0.5))
                maximum = float(node.config.get("max_seconds", minimum))
            except (TypeError, ValueError):
                return [f"{prefix}: delay values must be numbers."]
            if minimum < 0 or maximum < 0:
                return [f"{prefix}: delay cannot be negative."]
        return []

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
