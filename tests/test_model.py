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


def test_connect_replaces_existing_outgoing_edge() -> None:
    start = Node(NodeKind.START, "Start")
    first = Node(NodeKind.DELAY, "First")
    second = Node(NodeKind.STOP, "Second")
    workflow = Workflow(nodes=[start, first, second], edges=[Edge(start.id, first.id)])

    workflow.connect(start.id, second.id)

    assert workflow.edges == [Edge(start.id, second.id)]


def test_remove_node_also_removes_its_connections() -> None:
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Delay")
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(
        nodes=[start, delay, stop],
        edges=[Edge(start.id, delay.id), Edge(delay.id, stop.id)],
    )

    workflow.remove_node(delay.id)

    assert [node.id for node in workflow.nodes] == [start.id, stop.id]
    assert workflow.edges == []


def test_stop_cannot_connect_to_another_node() -> None:
    start = Node(NodeKind.START, "Start")
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(nodes=[start, stop])

    try:
        workflow.connect(stop.id, start.id)
    except ValueError as exc:
        assert str(exc) == "A Stop node cannot have an outgoing connection."
    else:
        raise AssertionError("Expected invalid connection to fail")


def test_find_image_requires_a_template() -> None:
    start = Node(NodeKind.START, "Start")
    find = Node(NodeKind.FIND_IMAGE, "Find button", config={"threshold": 0.8})
    workflow = Workflow(nodes=[start, find], edges=[Edge(start.id, find.id)])

    assert "Find button: choose a template image." in workflow.validate()


def test_delay_cannot_be_negative() -> None:
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Wait", config={"min_seconds": -1, "max_seconds": 1})
    workflow = Workflow(nodes=[start, delay], edges=[Edge(start.id, delay.id)])

    assert "Wait: delay cannot be negative." in workflow.validate()
