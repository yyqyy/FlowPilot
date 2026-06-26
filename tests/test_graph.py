import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from flowpilot.graph import GraphScene
from flowpilot.model import Edge, Node, NodeKind, Workflow


def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_connect_nodes_replaces_rendered_outgoing_edge() -> None:
    application()
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Delay")
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(
        nodes=[start, delay, stop],
        edges=[Edge(start.id, delay.id)],
    )
    scene = GraphScene(workflow)

    scene.connect_nodes(start.id, stop.id)

    assert workflow.edges == [Edge(start.id, stop.id)]
    assert len(scene.edge_items) == 1
    assert scene.edge_items[0].target.node.id == stop.id


def test_deleting_a_selected_node_removes_connected_edges() -> None:
    application()
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Delay")
    workflow = Workflow(nodes=[start, delay], edges=[Edge(start.id, delay.id)])
    scene = GraphScene(workflow)
    scene.node_items[delay.id].setSelected(True)

    scene.delete_selected()

    assert [node.id for node in workflow.nodes] == [start.id]
    assert workflow.edges == []
    assert delay.id not in scene.node_items
