from pathlib import Path

from flowpilot.model import Edge, Node, NodeKind, Workflow


def test_workflow_round_trip(tmp_path: Path) -> None:
    start = Node(NodeKind.START, "Start")
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow("Demo", [start, stop], [Edge(start.id, stop.id)])
    path = tmp_path / "demo.flowpilot.json"

    workflow.save(path)
    loaded = Workflow.load(path)

    assert loaded.name == "Demo"
    assert loaded.nodes[0].kind == NodeKind.START
    assert loaded.validate() == []


def test_workflow_requires_one_start() -> None:
    workflow = Workflow(nodes=[Node(NodeKind.STOP, "Stop")])
    assert "exactly one Start" in workflow.validate()[0]

