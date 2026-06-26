from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
)

from flowpilot.model import Edge, Node, NodeKind, Workflow


NODE_WIDTH = 190
NODE_HEIGHT = 76
PORT_SIZE = 14

NODE_COLORS = {
    NodeKind.START: "#22c55e",
    NodeKind.FIND_IMAGE: "#06b6d4",
    NodeKind.CLICK: "#8b5cf6",
    NodeKind.TYPE_TEXT: "#f59e0b",
    NodeKind.DELAY: "#64748b",
    NodeKind.STOP: "#ef4444",
}


class PortItem(QGraphicsEllipseItem):
    def __init__(self, node_item: "NodeItem", direction: str):
        super().__init__(-PORT_SIZE / 2, -PORT_SIZE / 2, PORT_SIZE, PORT_SIZE, node_item)
        self.node_item = node_item
        self.direction = direction
        self.setBrush(QColor("#e2e8f0"))
        self.setPen(QPen(QColor("#0f172a"), 2))
        self.setZValue(3)
        self.setCursor(Qt.CursorShape.CrossCursor)
        x = 0 if direction == "input" else NODE_WIDTH
        self.setPos(x, NODE_HEIGHT / 2)

    def center_in_scene(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))


class EdgeItem(QGraphicsPathItem):
    def __init__(self, edge: Edge, source: "NodeItem", target: "NodeItem"):
        super().__init__()
        self.edge = edge
        self.source = source
        self.target = target
        self.setPen(QPen(QColor("#64748b"), 3))
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_path()

    def update_path(self) -> None:
        start = self.source.output_port.center_in_scene()
        end = self.target.input_port.center_in_scene()
        distance = max(70.0, abs(end.x() - start.x()) * 0.5)
        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + distance, start.y()),
            QPointF(end.x() - distance, end.y()),
            end,
        )
        self.setPath(path)


class NodeItem(QGraphicsRectItem):
    def __init__(self, node: Node):
        super().__init__(0, 0, NODE_WIDTH, NODE_HEIGHT)
        self.node = node
        self.edges: list[EdgeItem] = []
        self.setPos(QPointF(node.x, node.y))
        self.setBrush(QColor("#172033"))
        self.setPen(QPen(QColor(NODE_COLORS[node.kind]), 2))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.title_item = QGraphicsTextItem(node.title, self)
        self.title_item.setDefaultTextColor(QColor("#f8fafc"))
        self.title_item.setPos(12, 10)
        kind = QGraphicsTextItem(node.kind.value.replace("_", " "), self)
        kind.setDefaultTextColor(QColor("#94a3b8"))
        kind.setPos(12, 40)
        self.input_port = None if node.kind == NodeKind.START else PortItem(self, "input")
        self.output_port = None if node.kind == NodeKind.STOP else PortItem(self, "output")

    def sync(self) -> None:
        self.node.x = self.pos().x()
        self.node.y = self.pos().y()

    def refresh_title(self) -> None:
        self.title_item.setPlainText(self.node.title)

    def itemChange(self, change, value):  # noqa: N802
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.sync()
            for edge in self.edges:
                edge.update_path()
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.mark_changed()
        return super().itemChange(change, value)


class GraphScene(QGraphicsScene):
    workflow_changed = Signal()
    node_selected = Signal(object)
    message = Signal(str)

    def __init__(self, workflow: Workflow, parent=None):
        super().__init__(parent)
        self.workflow = workflow
        self.node_items: dict[str, NodeItem] = {}
        self.edge_items: list[EdgeItem] = []
        self._drag_source: PortItem | None = None
        self._drag_path: QGraphicsPathItem | None = None
        self.selectionChanged.connect(self._selection_changed)
        self.render_workflow()

    def render_workflow(self) -> None:
        self.clear()
        self.node_items.clear()
        self.edge_items.clear()
        for node in self.workflow.nodes:
            item = NodeItem(node)
            self.node_items[node.id] = item
            self.addItem(item)
        for edge in self.workflow.edges:
            self._add_edge_item(edge)

    def add_node(self, node: Node) -> NodeItem:
        self.workflow.nodes.append(node)
        item = NodeItem(node)
        self.node_items[node.id] = item
        self.addItem(item)
        self.clearSelection()
        item.setSelected(True)
        self.mark_changed()
        return item

    def connect_nodes(self, source_id: str, target_id: str) -> None:
        try:
            self.workflow.connect(source_id, target_id)
        except (KeyError, ValueError) as exc:
            self.message.emit(str(exc))
            return
        self._rebuild_edges()
        self.mark_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        edge_keys = [
            (item.edge.source, item.edge.target) for item in selected if isinstance(item, EdgeItem)
        ]
        node_ids = [item.node.id for item in selected if isinstance(item, NodeItem)]
        for source, target in edge_keys:
            self.workflow.remove_edge(source, target)
        for node_id in node_ids:
            self.workflow.remove_node(node_id)
        if edge_keys or node_ids:
            self.render_workflow()
            self.mark_changed()

    def mark_changed(self) -> None:
        self.workflow_changed.emit()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):  # noqa: N802
        item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
        if isinstance(item, PortItem) and item.direction == "output":
            self._drag_source = item
            self._drag_path = QGraphicsPathItem()
            self._drag_path.setPen(QPen(QColor("#38bdf8"), 3, Qt.PenStyle.DashLine))
            self._drag_path.setZValue(5)
            self.addItem(self._drag_path)
            self._update_drag_path(event.scenePos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):  # noqa: N802
        if self._drag_source is not None:
            self._update_drag_path(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):  # noqa: N802
        if self._drag_source is not None:
            source = self._drag_source
            target = self._port_at(event.scenePos(), "input")
            self._clear_drag()
            if target is not None:
                self.connect_nodes(source.node_item.node.id, target.node_item.node.id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _port_at(self, position: QPointF, direction: str) -> PortItem | None:
        for item in self.items(position):
            if isinstance(item, PortItem) and item.direction == direction:
                return item
        return None

    def _update_drag_path(self, end: QPointF) -> None:
        if self._drag_source is None or self._drag_path is None:
            return
        start = self._drag_source.center_in_scene()
        distance = max(70.0, abs(end.x() - start.x()) * 0.5)
        path = QPainterPath(start)
        path.cubicTo(
            QPointF(start.x() + distance, start.y()),
            QPointF(end.x() - distance, end.y()),
            end,
        )
        self._drag_path.setPath(path)

    def _clear_drag(self) -> None:
        if self._drag_path is not None:
            self.removeItem(self._drag_path)
        self._drag_path = None
        self._drag_source = None

    def _rebuild_edges(self) -> None:
        for item in self.edge_items:
            self.removeItem(item)
        for node_item in self.node_items.values():
            node_item.edges.clear()
        self.edge_items.clear()
        for edge in self.workflow.edges:
            self._add_edge_item(edge)

    def _add_edge_item(self, edge: Edge) -> None:
        source = self.node_items.get(edge.source)
        target = self.node_items.get(edge.target)
        if source is None or target is None or source.output_port is None or target.input_port is None:
            return
        item = EdgeItem(edge, source, target)
        source.edges.append(item)
        target.edges.append(item)
        self.edge_items.append(item)
        self.addItem(item)

    def _selection_changed(self) -> None:
        selected_nodes = [item for item in self.selectedItems() if isinstance(item, NodeItem)]
        self.node_selected.emit(selected_nodes[0].node if len(selected_nodes) == 1 else None)
