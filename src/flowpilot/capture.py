from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QDialog


def normalized_selection(start: QPoint, end: QPoint) -> QRect:
    return QRect(
        min(start.x(), end.x()),
        min(start.y(), end.y()),
        abs(end.x() - start.x()),
        abs(end.y() - start.y()),
    )


class CaptureOverlay(QDialog):
    """Full-screen region picker for the primary display."""

    captured = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("No display is available for screen capture.")
        self._screenshot = screen.grabWindow(0)
        self._start: QPoint | None = None
        self._end: QPoint | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(screen.geometry())

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._screenshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))
        selection = self.selection_rect()
        if not selection.isNull():
            painter.drawPixmap(selection, self._screenshot, selection)
            painter.setPen(QPen(QColor("#38bdf8"), 2))
            painter.drawRect(selection)

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._end = self._start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        if self._start is not None:
            self._end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._end = event.position().toPoint()
        selection = self.selection_rect()
        if selection.width() >= 3 and selection.height() >= 3:
            self.captured.emit(self._screenshot.copy(selection))
            self.accept()
        else:
            self._start = None
            self._end = None
            self.update()

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def selection_rect(self) -> QRect:
        if self._start is None or self._end is None:
            return QRect()
        return normalized_selection(self._start, self._end)
