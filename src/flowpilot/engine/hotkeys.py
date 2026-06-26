from __future__ import annotations

from collections.abc import Callable


class HotkeyBinder:
    """Thin wrapper over the `keyboard` library that degrades gracefully.

    If global hotkeys are unavailable (library missing or no permission), every
    method is a safe no-op and `available` is False — the API still runs tasks.
    """

    def __init__(self) -> None:
        self._handles: list[object] = []
        self._kb = None
        try:
            import keyboard

            self._kb = keyboard
            self.available = True
        except Exception:  # pragma: no cover - platform dependent
            self.available = False

    def clear(self) -> None:
        if self._kb is None:
            self._handles = []
            return
        for handle in self._handles:
            try:
                self._kb.remove_hotkey(handle)
            except (KeyError, ValueError):
                pass
        self._handles = []

    def bind(self, combo: str, callback: Callable[[], None]) -> bool:
        if not combo.strip() or self._kb is None:
            return False
        try:
            handle = self._kb.add_hotkey(combo, callback, suppress=False)
        except (ValueError, ImportError):  # pragma: no cover - platform dependent
            return False
        self._handles.append(handle)
        return True
