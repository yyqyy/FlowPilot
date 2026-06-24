from PySide6.QtCore import QPoint, QRect

from flowpilot.capture import normalized_selection


def test_selection_is_normalized_when_dragging_up_and_left() -> None:
    assert normalized_selection(QPoint(80, 60), QPoint(20, 10)) == QRect(20, 10, 60, 50)
