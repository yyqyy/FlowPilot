from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QCloseEvent, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from flowpilot.capture import CaptureOverlay
from flowpilot.executor import WorkflowExecutor
from flowpilot.graph import GraphScene
from flowpilot.inspector import NodeInspector
from flowpilot.model import Edge, Node, NodeKind, Workflow
from flowpilot.screen import ScreenMatcher


class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QColor("#0b1020"))
        self.setSceneRect(-2000, -2000, 4000, 4000)

    def wheelEvent(self, event):  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlowPilot — Visual Automation Studio")
        self.resize(1180, 760)
        self.current_path: Path | None = None
        self.dirty = False
        self.workflow = self._starter_workflow()
        self.scene: GraphScene
        self.view: GraphView
        self.inspector = NodeInspector(self)
        self._build_editor()
        self._build_toolbar()
        self._build_inspector()
        self._set_workflow(self.workflow)
        self.statusBar().showMessage("Dry-run mode is ON — input control is disabled")

    def _starter_workflow(self) -> Workflow:
        start = Node(NodeKind.START, "Start", 0, 0)
        delay = Node(NodeKind.DELAY, "Random delay", 260, 0, {"min_seconds": 0.5, "max_seconds": 1.5})
        stop = Node(NodeKind.STOP, "Stop", 520, 0)
        return Workflow(
            name="First workflow",
            nodes=[start, delay, stop],
            edges=[Edge(start.id, delay.id), Edge(delay.id, stop.id)],
        )

    def _build_editor(self) -> None:
        self.scene = GraphScene(self.workflow, self)
        self.view = GraphView(self.scene)
        self.setCentralWidget(self.view)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Workflow", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, shortcut, callback in [
            ("New", QKeySequence.StandardKey.New, self.new_workflow),
            ("Open", QKeySequence.StandardKey.Open, self.open_workflow),
            ("Save", QKeySequence.StandardKey.Save, self.save_workflow),
        ]:
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            toolbar.addAction(action)
        save_as = QAction("Save as", self)
        save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as.triggered.connect(self.save_workflow_as)
        toolbar.addAction(save_as)
        delete = QAction("Delete", self)
        delete.setShortcut(QKeySequence.StandardKey.Delete)
        delete.triggered.connect(lambda: self.scene.delete_selected())
        self.addAction(delete)
        toolbar.addSeparator()
        run = QAction("▶ Run dry", self)
        run.triggered.connect(self.run_dry)
        toolbar.addAction(run)
        test_image = QAction("◎ Test image", self)
        test_image.triggered.connect(self.test_image)
        toolbar.addAction(test_image)
        capture_image = QAction("▣ Capture template", self)
        capture_image.triggered.connect(self.capture_template)
        toolbar.addAction(capture_image)
        toolbar.addSeparator()
        for kind, label in [
            (NodeKind.FIND_IMAGE, "+ Find image"),
            (NodeKind.CLICK, "+ Click"),
            (NodeKind.TYPE_TEXT, "+ Type text"),
            (NodeKind.DELAY, "+ Delay"),
        ]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, value=kind: self.add_node(value))
            toolbar.addAction(action)

    def _build_inspector(self) -> None:
        dock = QDockWidget("Node properties", self)
        dock.setObjectName("node-properties")
        dock.setWidget(self.inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.inspector.changed.connect(self._inspector_changed)

    def _set_workflow(self, workflow: Workflow) -> None:
        self.workflow = workflow
        old_scene = self.scene
        self.scene = GraphScene(workflow, self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.scene.workflow_changed.connect(self._mark_dirty)
        self.scene.node_selected.connect(self.inspector.set_node)
        self.scene.message.connect(self.statusBar().showMessage)
        self.view.setScene(self.scene)
        old_scene.deleteLater()
        self.inspector.set_node(None)
        self.dirty = False
        self._update_title()

    def add_node(self, kind: NodeKind) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        defaults = {
            NodeKind.FIND_IMAGE: {"template": "", "threshold": 0.85},
            NodeKind.CLICK: {"target": "fixed", "x": 0, "y": 0},
            NodeKind.TYPE_TEXT: {"text": ""},
            NodeKind.DELAY: {"min_seconds": 0.5, "max_seconds": 1.5},
        }
        node = Node(
            kind,
            kind.value.replace("_", " ").title(),
            center.x(),
            center.y(),
            defaults.get(kind, {}),
        )
        self.scene.add_node(node)

    def run_dry(self) -> None:
        messages: list[str] = []
        try:
            WorkflowExecutor(self.workflow, dry_run=True, log=messages.append).run()
        except Exception as exc:  # UI boundary
            QMessageBox.critical(self, "Workflow error", str(exc))
            return
        QMessageBox.information(self, "Dry-run result", "\n".join(messages))

    def test_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a template image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not filename:
            return
        try:
            result = ScreenMatcher().find_template(Path(filename), threshold=0.8)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Image match failed", str(exc))
            return
        if result is None:
            QMessageBox.warning(self, "No match", "The image was not found on the screen.")
            return
        QMessageBox.information(
            self,
            "Match found",
            f"Center: {result.center[0]}, {result.center[1]}\n"
            f"Confidence: {result.confidence:.1%}",
        )

    def capture_template(self) -> None:
        self.statusBar().showMessage("FlowPilot will hide; drag a box around the target image")
        self.hide()
        QTimer.singleShot(700, self._open_capture_overlay)

    def _open_capture_overlay(self) -> None:
        overlay = CaptureOverlay()
        selected = []
        overlay.captured.connect(selected.append)
        overlay.exec()
        self.show()
        self.activateWindow()
        if not selected:
            self.statusBar().showMessage("Capture cancelled")
            return

        template_dir = Path.cwd() / "assets" / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("template-%Y%m%d-%H%M%S.png")
        template_path = template_dir / filename
        if not selected[0].save(str(template_path), "PNG"):
            QMessageBox.critical(self, "Capture failed", f"Could not save {template_path}")
            return

        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = Node(
            NodeKind.FIND_IMAGE,
            "Find captured image",
            center.x(),
            center.y(),
            {"template": str(template_path), "threshold": 0.85},
        )
        self.scene.add_node(node)
        self.statusBar().showMessage(f"Saved template: {template_path.name}")

    def new_workflow(self) -> None:
        if not self._maybe_save():
            return
        start = Node(NodeKind.START, "Start", 0, 0)
        stop = Node(NodeKind.STOP, "Stop", 280, 0)
        self.current_path = None
        self._set_workflow(Workflow("Untitled workflow", [start, stop], [Edge(start.id, stop.id)]))

    def open_workflow(self) -> None:
        if not self._maybe_save():
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open workflow",
            "",
            "FlowPilot workflow (*.flowpilot.json);;JSON files (*.json)",
        )
        if not filename:
            return
        try:
            workflow = Workflow.load(Path(filename))
            errors = workflow.validate()
            if errors:
                raise ValueError("\n".join(errors))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not open workflow", str(exc))
            return
        self.current_path = Path(filename)
        self._set_workflow(workflow)
        self.statusBar().showMessage(f"Opened {self.current_path.name}")

    def save_workflow(self) -> bool:
        if self.current_path is None:
            return self.save_workflow_as()
        try:
            self.workflow.save(self.current_path)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save workflow", str(exc))
            return False
        self.dirty = False
        self._update_title()
        self.statusBar().showMessage(f"Saved {self.current_path.name}")
        return True

    def save_workflow_as(self) -> bool:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save workflow",
            str(self.current_path or Path.cwd() / "workflow.flowpilot.json"),
            "FlowPilot workflow (*.flowpilot.json)",
        )
        if not filename:
            return False
        path = Path(filename)
        if not path.name.endswith(".flowpilot.json"):
            path = path.with_name(f"{path.name}.flowpilot.json")
        self.current_path = path
        return self.save_workflow()

    def closeEvent(self, event: QCloseEvent):  # noqa: N802
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()

    def _inspector_changed(self) -> None:
        node = self.inspector.node
        if node is not None:
            item = self.scene.node_items.get(node.id)
            if item is not None:
                item.refresh_title()
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        self.dirty = True
        self._update_title()

    def _update_title(self) -> None:
        name = self.current_path.name if self.current_path else self.workflow.name
        marker = " *" if self.dirty else ""
        self.setWindowTitle(f"{name}{marker} — FlowPilot")

    def _maybe_save(self) -> bool:
        if not self.dirty:
            return True
        choice = QMessageBox.warning(
            self,
            "Unsaved changes",
            "Save changes to the current workflow?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save_workflow()
        return choice == QMessageBox.StandardButton.Discard


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
