from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from flowpilot.model import Node, NodeKind


class NodeInspector(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.node: Node | None = None
        self._title = QLabel("Properties")
        self._form_host = QWidget()
        self._form = QFormLayout(self._form_host)
        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._form_host)
        layout.addStretch(1)
        self.setMinimumWidth(280)
        self.set_node(None)

    def set_node(self, node: Node | None) -> None:
        self.node = node
        self._clear_form()
        if node is None:
            self._title.setText("Properties")
            self._form.addRow(QLabel("Select one node to edit it."))
            return
        self._title.setText(node.kind.value.replace("_", " ").title())
        title = QLineEdit(node.title)
        title.textChanged.connect(self._set_title)
        self._form.addRow("Name", title)
        builders: dict[NodeKind, Callable[[], None]] = {
            NodeKind.FIND_IMAGE: self._build_find_image,
            NodeKind.CLICK: self._build_click,
            NodeKind.TYPE_TEXT: self._build_type_text,
            NodeKind.DELAY: self._build_delay,
        }
        builder = builders.get(node.kind)
        if builder:
            builder()

    def _build_find_image(self) -> None:
        assert self.node is not None
        template = QLineEdit(str(self.node.config.get("template", "")))
        browse = QPushButton("Browse")
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(template)
        row_layout.addWidget(browse)
        template.textChanged.connect(lambda value: self._set_config("template", value))
        browse.clicked.connect(lambda: self._choose_template(template))
        confidence = QDoubleSpinBox()
        confidence.setRange(0.01, 1.0)
        confidence.setSingleStep(0.01)
        confidence.setDecimals(2)
        confidence.setValue(float(self.node.config.get("threshold", 0.85)))
        confidence.valueChanged.connect(lambda value: self._set_config("threshold", value))
        self._form.addRow("Template", row)
        self._form.addRow("Confidence", confidence)

    def _build_click(self) -> None:
        assert self.node is not None
        target = QComboBox()
        target.addItem("Fixed position", "fixed")
        target.addItem("Last image match", "last_match")
        value = str(self.node.config.get("target", "fixed"))
        target.setCurrentIndex(max(0, target.findData(value)))
        target.currentIndexChanged.connect(
            lambda: self._set_config("target", target.currentData())
        )
        x = self._coordinate_spinbox(int(self.node.config.get("x", 0)))
        y = self._coordinate_spinbox(int(self.node.config.get("y", 0)))
        x.valueChanged.connect(lambda value: self._set_config("x", value))
        y.valueChanged.connect(lambda value: self._set_config("y", value))
        self._form.addRow("Target", target)
        self._form.addRow("X", x)
        self._form.addRow("Y", y)

    def _build_type_text(self) -> None:
        assert self.node is not None
        text = QTextEdit(str(self.node.config.get("text", "")))
        text.setMinimumHeight(100)
        text.textChanged.connect(lambda: self._set_config("text", text.toPlainText()))
        self._form.addRow("Text", text)

    def _build_delay(self) -> None:
        assert self.node is not None
        minimum = self._seconds_spinbox(float(self.node.config.get("min_seconds", 0.5)))
        maximum = self._seconds_spinbox(
            float(self.node.config.get("max_seconds", self.node.config.get("min_seconds", 0.5)))
        )
        minimum.valueChanged.connect(lambda value: self._set_config("min_seconds", value))
        maximum.valueChanged.connect(lambda value: self._set_config("max_seconds", value))
        self._form.addRow("Minimum seconds", minimum)
        self._form.addRow("Maximum seconds", maximum)

    def _set_title(self, value: str) -> None:
        if self.node is not None:
            self.node.title = value.strip() or self.node.kind.value.replace("_", " ").title()
            self.changed.emit()

    def _set_config(self, key: str, value) -> None:
        if self.node is not None:
            self.node.config[key] = value
            self.changed.emit()

    def _choose_template(self, target: QLineEdit) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a template image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if filename:
            target.setText(filename)

    def _clear_form(self) -> None:
        while self._form.count():
            item = self._form.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _coordinate_spinbox(value: int) -> QSpinBox:
        control = QSpinBox()
        control.setRange(-100_000, 100_000)
        control.setValue(value)
        return control

    @staticmethod
    def _seconds_spinbox(value: float) -> QDoubleSpinBox:
        control = QDoubleSpinBox()
        control.setRange(0, 86_400)
        control.setDecimals(2)
        control.setSingleStep(0.1)
        control.setValue(value)
        return control
