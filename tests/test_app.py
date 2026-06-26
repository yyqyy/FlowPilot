import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from flowpilot.app import MainWindow
from flowpilot.executor import WorkflowExecutor
from flowpilot.model import NodeKind


def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_main_window_starts_clean_and_valid() -> None:
    application()
    window = MainWindow()

    assert not window.dirty
    assert window.workflow.validate() == []
    assert window.view.scene() is window.scene


def test_adding_a_node_marks_the_workflow_dirty() -> None:
    application()
    window = MainWindow()

    window.add_node(NodeKind.CLICK)

    assert window.dirty
    assert any(node.kind == NodeKind.CLICK for node in window.workflow.nodes)


def test_connect_and_delete_keep_model_and_scene_in_sync() -> None:
    application()
    window = MainWindow()
    start = next(n for n in window.workflow.nodes if n.kind == NodeKind.START)
    window.add_node(NodeKind.CLICK)
    click = next(n for n in window.workflow.nodes if n.kind == NodeKind.CLICK)

    window.scene.connect_nodes(start.id, click.id)
    assert any(e.source == start.id and e.target == click.id for e in window.workflow.edges)

    window.scene.node_items[click.id].setSelected(True)
    window.scene.delete_selected()

    assert click.id not in window.scene.node_items
    assert all(click.id not in (e.source, e.target) for e in window.workflow.edges)


def test_starter_workflow_completes_a_dry_run() -> None:
    application()
    window = MainWindow()
    messages: list[str] = []

    WorkflowExecutor(window.workflow, dry_run=True, log=messages.append).run()

    assert messages[-1] == "Workflow completed."


def test_new_workflow_creates_a_fresh_valid_graph() -> None:
    application()
    window = MainWindow()
    original_ids = {node.id for node in window.workflow.nodes}

    window.new_workflow()  # window is clean, so this skips the save prompt

    new_ids = {node.id for node in window.workflow.nodes}
    assert new_ids.isdisjoint(original_ids)
    assert {node.kind for node in window.workflow.nodes} == {NodeKind.START, NodeKind.STOP}
    assert not window.dirty
    assert window.inspector.node is None
    assert window.view.scene() is window.scene
    assert window.workflow.validate() == []
