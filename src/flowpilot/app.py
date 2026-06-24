from __future__ import annotations

from pathlib import Path
import sys
from datetime import datetime

from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QAction, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from flowpilot.executor import WorkflowExecutor
from flowpilot.capture import CaptureOverlay
from flowpilot.model import Edge, Node, NodeKind, Workflow
from flowpilot.screen import ScreenMatcher


NODE_COLORS = {
    NodeKind.START: "#22c55e",
    NodeKind.FIND_IMAGE: "#06b6d4",
    NodeKind.CLICK: "#8b5cf6",
    NodeKind.TYPE_TEXT: "#f59e0b",
    NodeKind.DELAY: "#64748b",
    NodeKind.STOP: "#ef4444",
}


class NodeItem(QGraphicsRectItem):
    def __init__(self, node: Node):
        super().__init__(0, 0, 180, 72)
        self.node = node
        self.setPos(QPointF(node.x, node.y))
        self.setBrush(QColor("#172033"))
        self.setPen(QPen(QColor(NODE_COLORS[node.kind]), 2))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        title = QGraphicsTextItem(node.title, self)
        title.setDefaultTextColor(QColor("#f8fafc"))
        title.setPos(12, 10)
        kind = QGraphicsTextItem(node.kind.value.replace("_", " "), self)
        kind.setDefaultTextColor(QColor("#94a3b8"))
        kind.setPos(12, 36)

    def sync(self) -> None:
        self.node.x = self.pos().x()
        self.node.y = self.pos().y()


class GraphView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene):
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
        self.workflow = self._starter_workflow()
        self.scene = QGraphicsScene(self)
        self.view = GraphView(self.scene)
        self.setCentralWidget(self.view)
        self._build_toolbar()
        self._render_workflow()
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

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Workflow", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
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

    def _render_workflow(self) -> None:
        self.scene.clear()
        for node in self.workflow.nodes:
            self.scene.addItem(NodeItem(node))

    def add_node(self, kind: NodeKind) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        node = Node(kind, kind.value.replace("_", " ").title(), center.x(), center.y())
        self.workflow.nodes.append(node)
        self.scene.addItem(NodeItem(node))

    def run_dry(self) -> None:
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                item.sync()
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
        self.workflow.nodes.append(node)
        self.scene.addItem(NodeItem(node))
        self.statusBar().showMessage(f"Saved template: {template_path.name}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
