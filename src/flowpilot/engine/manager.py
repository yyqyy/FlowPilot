from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

from flowpilot.engine.actions import InputController
from flowpilot.engine.hotkeys import HotkeyBinder
from flowpilot.engine.runner import Locator, run_task
from flowpilot.engine.store import TaskStore
from flowpilot.screen import ScreenMatcher


class EngineRuntime:
    """Owns task execution: run/stop/restart, recent log, and hotkey binding.

    Re-triggering a running task aborts the in-flight run and starts a fresh one
    (press-again-restarts semantics).
    """

    def __init__(
        self,
        store: TaskStore,
        *,
        locator: Locator | None = None,
        controller: InputController | None = None,
        binder: HotkeyBinder | None = None,
    ) -> None:
        self.store = store
        self.locator: Locator = locator or ScreenMatcher()
        self._controller = controller
        self.binder = binder or HotkeyBinder()
        self._runs: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self._log: deque[str] = deque(maxlen=300)
        self.refresh_hotkeys()

    # -- logging -----------------------------------------------------------
    def log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        with self._lock:
            self._log.append(f"{stamp}  {message}")

    def recent_log(self) -> list[str]:
        with self._lock:
            return list(self._log)

    # -- run control -------------------------------------------------------
    def _controller_instance(self) -> InputController:
        if self._controller is None:
            from flowpilot.engine.actions import PyAutoGuiController

            self._controller = PyAutoGuiController()
        return self._controller

    def run(self, task_id: str, *, restart: bool = False) -> None:
        task = self.store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        if self.is_running(task_id):
            if not restart:
                # One press = one run. A second trigger while running is ignored
                # rather than restarting, so accidental double-taps don't look
                # like "nothing happened".
                self.log(f"⏸ {task.name} 正在运行，忽略本次触发")
                return
            self.stop(task_id)  # explicit restart: abort the in-flight run first

        stop = threading.Event()
        controller = self._controller_instance()

        def worker(my_stop: threading.Event = stop) -> None:
            try:
                run_task(task, controller=controller, locator=self.locator, stop=my_stop, log=self.log)
            except Exception as exc:  # engine boundary
                self.log(f"运行出错：{exc}")
            finally:
                with self._lock:
                    if self._runs.get(task_id) is my_stop:
                        self._runs.pop(task_id, None)
                        self._threads.pop(task_id, None)

        thread = threading.Thread(target=worker, name=f"task-{task_id}", daemon=True)
        with self._lock:
            self._runs[task_id] = stop
            self._threads[task_id] = thread
        self.log(f"▶ 运行：{task.name}")
        thread.start()

    def stop(self, task_id: str) -> None:
        with self._lock:
            stop = self._runs.get(task_id)
        if stop is not None:
            stop.set()

    def stop_all(self) -> None:
        with self._lock:
            events = list(self._runs.values())
        for stop in events:
            stop.set()

    def is_running(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._runs

    def running_ids(self) -> list[str]:
        with self._lock:
            return list(self._runs.keys())

    # -- hotkeys -----------------------------------------------------------
    def refresh_hotkeys(self) -> None:
        self.binder.clear()
        for task in self.store.list():
            if not task.enabled:
                continue
            if task.hotkey:
                self.binder.bind(task.hotkey, self._trigger(task.id))
            if task.stop_hotkey:
                self.binder.bind(task.stop_hotkey, self._stopper(task.id))

    def _trigger(self, task_id: str) -> Callable[[], None]:
        return lambda: self.run(task_id)

    def _stopper(self, task_id: str) -> Callable[[], None]:
        return lambda: self.stop(task_id)
