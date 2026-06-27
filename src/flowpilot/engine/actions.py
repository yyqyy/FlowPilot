from __future__ import annotations

import base64
import subprocess
import sys
from typing import Protocol, runtime_checkable

import cv2
import numpy as np


def decode_template(data: str) -> np.ndarray | None:
    """Decode a base64 (optionally a `data:` URL) PNG/JPEG into a BGR image."""
    if not data:
        return None
    payload = data.split(",", 1)[1] if data.startswith("data:") else data
    try:
        raw = np.frombuffer(base64.b64decode(payload), np.uint8)
    except (ValueError, TypeError):
        return None
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, cv2.IMREAD_COLOR)


@runtime_checkable
class InputController(Protocol):
    """Boundary for everything that touches the real mouse/keyboard/OS.

    Swapped for a recording fake in tests so the suite never moves real input.
    """

    def click(self, x: int, y: int, *, button: str = "left", clicks: int = 1) -> None: ...

    def type_text(self, text: str) -> None: ...

    def press(self, combo: str) -> None: ...

    def launch(self, path: str, args: str = "", wait: float = 0.0) -> None: ...

    def screen_size(self) -> tuple[int, int]: ...

    def drag_path(
        self, points: list[tuple[int, int]], durations: list[float], *, button: str = "left"
    ) -> None: ...


class PyAutoGuiController:
    """Real input via PyAutoGUI; app launching via the OS."""

    def __init__(self) -> None:
        import pyautogui

        pyautogui.FAILSAFE = True  # slam mouse to a corner to abort
        self._gui = pyautogui

    def click(self, x: int, y: int, *, button: str = "left", clicks: int = 1) -> None:
        gui_button = "right" if button == "right" else "left"
        self._gui.click(x=x, y=y, clicks=clicks, button=gui_button)

    def type_text(self, text: str) -> None:
        if not text:
            return
        # PyAutoGUI's write() can only emit ASCII; anything else (e.g. Chinese)
        # is silently dropped, so paste non-ASCII text via the clipboard.
        if text.isascii():
            self._gui.write(text, interval=0.02)
            return
        if self._paste(text):
            return
        try:
            import keyboard

            keyboard.write(text)
        except Exception:
            self._gui.write(text, interval=0.02)

    def _paste(self, text: str) -> bool:
        try:
            import pyperclip

            pyperclip.copy(text)
        except Exception:
            return False
        self._gui.hotkey("ctrl", "v")
        return True

    def press(self, combo: str) -> None:
        keys = [part.strip().lower() for part in combo.split("+") if part.strip()]
        if not keys:
            return
        if len(keys) == 1:
            self._gui.press(keys[0])
        else:
            self._gui.hotkey(*keys)

    def launch(self, path: str, args: str = "", wait: float = 0.0) -> None:
        if not path.strip():
            return
        argv = [path, *args.split()] if args.strip() else [path]
        if sys.platform == "win32":
            subprocess.Popen(argv, shell=False)
        else:
            subprocess.Popen(argv)

    def screen_size(self) -> tuple[int, int]:
        size = self._gui.size()
        return int(size[0]), int(size[1])

    def drag_path(
        self, points: list[tuple[int, int]], durations: list[float], *, button: str = "left"
    ) -> None:
        """Press at the first point, drag through the rest, release at the last.
        `durations[i]` is the seconds spent dragging into point i+1."""
        if len(points) < 2:
            return
        gui_button = "right" if button == "right" else "left"
        self._gui.moveTo(points[0][0], points[0][1])
        self._gui.mouseDown(button=gui_button)
        try:
            for index in range(1, len(points)):
                seconds = durations[index - 1] if index - 1 < len(durations) else 0.3
                self._gui.moveTo(points[index][0], points[index][1], duration=max(0.0, seconds))
        finally:
            self._gui.mouseUp(button=gui_button)
