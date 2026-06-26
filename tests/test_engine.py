from __future__ import annotations

import base64
import threading
import time

import cv2
import numpy as np
from fastapi.testclient import TestClient

from flowpilot.engine.manager import EngineRuntime
from flowpilot.engine.model import Edge, Node, NodeKind, Task, TriggerMode
from flowpilot.engine.runner import run_task
from flowpilot.engine.server import create_app
from flowpilot.engine.store import TaskStore
from flowpilot.screen import MatchResult


def png_data_url() -> str:
    image = (np.random.default_rng(0).integers(0, 256, size=(8, 12, 3))).astype(np.uint8)
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return "data:image/png;base64," + base64.b64encode(buffer.tobytes()).decode()


class FakeController:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def click(self, x: int, y: int, *, button: str = "left", clicks: int = 1) -> None:
        self.events.append(("click", x, y, button, clicks))

    def type_text(self, text: str) -> None:
        self.events.append(("type", text))

    def press(self, combo: str) -> None:
        self.events.append(("press", combo))

    def launch(self, path: str, args: str = "", wait: float = 0.0) -> None:
        self.events.append(("launch", path, args, wait))


class FakeLocator:
    def __init__(self, result: MatchResult | None) -> None:
        self.result = result
        self.calls = 0

    def locate(self, template, *, threshold: float) -> MatchResult | None:
        self.calls += 1
        return self.result


class DummyBinder:
    available = False

    def clear(self) -> None:
        pass

    def bind(self, combo: str, callback) -> bool:
        return False


def test_find_click_clicks_match_center_with_offset() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(
        NodeKind.FIND_CLICK,
        "点按钮",
        config={"templateData": png_data_url(), "offsetX": 5, "offsetY": -3},
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, find, stop],
        edges=[Edge(start.id, find.id), Edge(find.id, stop.id)],
    )
    controller = FakeController()
    locator = FakeLocator(MatchResult(left=100, top=200, width=20, height=10, confidence=0.95))

    status = run_task(task, controller=controller, locator=locator, stop=threading.Event())

    assert status == "completed"
    assert ("click", 115, 202, "left", 1) in controller.events


def test_condition_branches_on_image_presence() -> None:
    def build() -> tuple[Task, FakeController]:
        start = Node(NodeKind.START, "开始")
        cond = Node(NodeKind.CONDITION, "看到了吗", config={"templateData": png_data_url()})
        yes = Node(NodeKind.TYPE_TEXT, "是", config={"text": "yes"})
        no = Node(NodeKind.TYPE_TEXT, "否", config={"text": "no"})
        stop = Node(NodeKind.STOP, "结束")
        task = Task(
            nodes=[start, cond, yes, no, stop],
            edges=[
                Edge(start.id, cond.id),
                Edge(cond.id, yes.id, "true"),
                Edge(cond.id, no.id, "false"),
                Edge(yes.id, stop.id),
                Edge(no.id, stop.id),
            ],
        )
        return task, FakeController()

    task, controller = build()
    run_task(task, controller=controller, locator=FakeLocator(MatchResult(0, 0, 4, 4, 0.9)),
             stop=threading.Event())
    assert ("type", "yes") in controller.events
    assert ("type", "no") not in controller.events

    task, controller = build()
    run_task(task, controller=controller, locator=FakeLocator(None), stop=threading.Event())
    assert ("type", "no") in controller.events
    assert ("type", "yes") not in controller.events


def test_times_mode_runs_repeat_times() -> None:
    start = Node(NodeKind.START, "开始")
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a"})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.TIMES,
        repeat=3,
        nodes=[start, key, stop],
        edges=[Edge(start.id, key.id), Edge(key.id, stop.id)],
    )
    controller = FakeController()
    run_task(task, controller=controller, locator=FakeLocator(None), stop=threading.Event())
    assert sum(1 for e in controller.events if e[0] == "press") == 3


def test_loop_mode_stops_when_event_set() -> None:
    stop_event = threading.Event()

    class StoppingController(FakeController):
        def press(self, combo: str) -> None:
            super().press(combo)
            stop_event.set()  # stop after the first iteration

    start = Node(NodeKind.START, "开始")
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a"})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.LOOP,
        nodes=[start, key, stop],
        edges=[Edge(start.id, key.id), Edge(key.id, stop.id)],
    )
    status = run_task(task, controller=StoppingController(), locator=FakeLocator(None), stop=stop_event)
    assert status == "stopped"
    assert sum(1 for e in StoppingController().events if e[0] == "press") == 0  # fresh instance


def test_store_round_trip(tmp_path) -> None:
    store = TaskStore(tmp_path)
    task = Task(name="存一下", hotkey="ctrl+alt+1", nodes=[Node(NodeKind.START, "开始")])
    store.save(task)

    loaded = store.get(task.id)
    assert loaded is not None
    assert loaded.name == "存一下"
    assert loaded.hotkey == "ctrl+alt+1"
    assert [t.id for t in store.list()] == [task.id]
    assert store.delete(task.id) is True
    assert store.get(task.id) is None


def test_manager_run_then_stop(tmp_path) -> None:
    store = TaskStore(tmp_path)
    start = Node(NodeKind.START, "开始")
    delay = Node(NodeKind.DELAY, "等", config={"min_seconds": 0.05, "max_seconds": 0.05})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.LOOP,
        nodes=[start, delay, stop],
        edges=[Edge(start.id, delay.id), Edge(delay.id, stop.id)],
    )
    store.save(task)
    runtime = EngineRuntime(store, locator=FakeLocator(None), controller=FakeController(),
                            binder=DummyBinder())

    runtime.run(task.id)
    assert runtime.is_running(task.id)
    runtime.stop(task.id)

    for _ in range(40):
        if not runtime.is_running(task.id):
            break
        time.sleep(0.05)
    assert not runtime.is_running(task.id)


def test_api_task_lifecycle(tmp_path) -> None:
    store = TaskStore(tmp_path)
    runtime = EngineRuntime(store, locator=FakeLocator(None), controller=FakeController(),
                            binder=DummyBinder())
    client = TestClient(create_app(runtime))

    created = client.post("/api/tasks", json={"name": "接口测试"}).json()
    task_id = created["id"]
    assert created["name"] == "接口测试"

    listing = client.get("/api/tasks").json()
    assert any(item["id"] == task_id for item in listing)

    created["hotkey"] = "ctrl+alt+9"
    updated = client.put(f"/api/tasks/{task_id}", json=created).json()
    assert updated["hotkey"] == "ctrl+alt+9"

    assert client.post(f"/api/tasks/{task_id}/run").json()["ok"] is True
    assert client.post(f"/api/tasks/{task_id}/stop").json()["ok"] is True

    assert client.delete(f"/api/tasks/{task_id}").json()["ok"] is True
    assert client.get(f"/api/tasks/{task_id}").status_code == 404
