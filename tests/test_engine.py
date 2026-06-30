from __future__ import annotations

import base64
import threading
import time

import cv2
import numpy as np
from fastapi.testclient import TestClient

from flowpilot.engine.manager import EngineRuntime
from flowpilot.engine.model import Edge, Node, NodeKind, Task, TriggerMode, Variable
from flowpilot.engine.runner import run_task
from flowpilot.engine.server import create_app
from flowpilot.engine.store import TaskStore
from flowpilot.screen import MatchResult


def png_data_url() -> str:
    image = (np.random.default_rng(0).integers(0, 256, size=(8, 12, 3))).astype(np.uint8)
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return "data:image/png;base64," + base64.b64encode(buffer.tobytes()).decode()


def ex(source: Node, handle: str, target: Node) -> Edge:
    """An exec wire from a node's source handle into a target's exec input."""
    return Edge(source=source.id, source_handle=handle, target=target.id, target_handle="exec")


def data(source: Node, handle: str, target: Node, target_handle: str) -> Edge:
    return Edge(
        source=source.id,
        source_handle=handle,
        target=target.id,
        target_handle=target_handle,
        kind="data",
    )


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

    def screen_size(self) -> tuple[int, int]:
        return (1920, 1080)

    def drag_path(self, points, durations, *, button: str = "left") -> None:
        self.events.append(("drag", list(points), list(durations), button))


class FakeLocator:
    def __init__(self, result: MatchResult | None) -> None:
        self.result = result
        self.calls = 0

    def locate(self, template, *, threshold: float) -> MatchResult | None:
        self.calls += 1
        return self.result


class FlakyLocator:
    """Returns None for the first `misses` calls, then `result` from then on —
    a screen that takes a few looks before the target renders."""

    def __init__(self, result: MatchResult | None, *, misses: int) -> None:
        self.result = result
        self.misses = misses
        self.calls = 0

    def locate(self, template, *, threshold: float) -> MatchResult | None:
        self.calls += 1
        return None if self.calls <= self.misses else self.result


class DummyBinder:
    available = False

    def clear(self) -> None:
        pass

    def bind(self, combo: str, callback) -> bool:
        return False


def run(task: Task, controller: FakeController, locator: FakeLocator) -> str:
    return run_task(task, controller=controller, locator=locator, stop=threading.Event())


# --------------------------------------------------------------------------- #
# find_click: success / fail exec outputs + 找到 data pin
# --------------------------------------------------------------------------- #
def test_find_click_success_clicks_center_with_offset() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(
        NodeKind.FIND_CLICK,
        "点按钮",
        config={"templateData": png_data_url(), "offsetX": 5, "offsetY": -3, "post_delay": 0},
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, find, stop], edges=[ex(start, "then", find), ex(find, "success", stop)])
    controller = FakeController()
    locator = FakeLocator(MatchResult(left=100, top=200, width=20, height=10, confidence=0.95))

    status = run(task, controller, locator)

    assert status == "completed"
    assert ("click", 115, 202, "left", 1) in controller.events


def test_find_click_fail_takes_fail_branch() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(NodeKind.FIND_CLICK, "点按钮", config={"templateData": png_data_url(), "post_delay": 0})
    failed = Node(NodeKind.TYPE_TEXT, "失败", config={"text": "failed", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, find, failed, stop],
        edges=[ex(start, "then", find), ex(find, "fail", failed), ex(failed, "then", stop)],
    )
    controller = FakeController()

    status = run(task, controller, FakeLocator(None))

    assert status == "completed"
    assert ("type", "failed") in controller.events
    assert not any(e[0] == "click" for e in controller.events)


def test_find_click_retries_until_image_appears() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(
        NodeKind.FIND_CLICK,
        "点按钮",
        config={
            "templateData": png_data_url(),
            "timeout": 5,
            "retry_interval": 0.01,
            "post_delay": 0,
        },
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, find, stop], edges=[ex(start, "then", find), ex(find, "success", stop)])
    controller = FakeController()
    locator = FlakyLocator(MatchResult(0, 0, 10, 10, 0.95), misses=2)

    status = run_task(task, controller=controller, locator=locator, stop=threading.Event())

    assert status == "completed"
    assert locator.calls == 3  # two misses, then the hit
    assert any(e[0] == "click" for e in controller.events)


def test_find_click_timeout_routes_fail_after_retrying() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(
        NodeKind.FIND_CLICK,
        "点按钮",
        config={
            "templateData": png_data_url(),
            "timeout": 0.1,
            "retry_interval": 0.01,
            "post_delay": 0,
        },
    )
    failed = Node(NodeKind.TYPE_TEXT, "失败", config={"text": "failed", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, find, failed, stop],
        edges=[ex(start, "then", find), ex(find, "fail", failed), ex(failed, "then", stop)],
    )
    controller = FakeController()
    locator = FakeLocator(None)

    status = run_task(task, controller=controller, locator=locator, stop=threading.Event())

    assert status == "completed"
    assert ("type", "failed") in controller.events
    assert locator.calls > 1  # it kept looking, didn't give up after one glance


def test_find_click_no_timeout_looks_once() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(NodeKind.FIND_CLICK, "点按钮", config={"templateData": png_data_url(), "post_delay": 0})
    failed = Node(NodeKind.TYPE_TEXT, "失败", config={"text": "failed", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, find, failed, stop],
        edges=[ex(start, "then", find), ex(find, "fail", failed), ex(failed, "then", stop)],
    )
    locator = FakeLocator(None)

    run_task(task, controller=FakeController(), locator=locator, stop=threading.Event())

    assert locator.calls == 1  # default timeout 0 keeps the original single-attempt behaviour


def test_condition_retries_until_image_appears() -> None:
    start = Node(NodeKind.START, "开始")
    cond = Node(
        NodeKind.CONDITION,
        "看图",
        config={
            "templateData": png_data_url(),
            "timeout": 5,
            "retry_interval": 0.01,
            "post_delay": 0,
        },
    )
    yes = Node(NodeKind.TYPE_TEXT, "真", config={"text": "yes", "post_delay": 0})
    no = Node(NodeKind.TYPE_TEXT, "假", config={"text": "no", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, cond, yes, no, stop],
        edges=[
            ex(start, "then", cond),
            ex(cond, "true", yes),
            ex(cond, "false", no),
            ex(yes, "then", stop),
            ex(no, "then", stop),
        ],
    )
    controller = FakeController()
    locator = FlakyLocator(MatchResult(0, 0, 4, 4, 0.9), misses=3)

    run_task(task, controller=controller, locator=locator, stop=threading.Event())

    assert ("type", "yes") in controller.events
    assert ("type", "no") not in controller.events


def test_find_type_without_template_types_directly() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(NodeKind.FIND_TYPE, "输入", config={"text": "你好", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, find, stop], edges=[ex(start, "then", find), ex(find, "success", stop)])
    controller = FakeController()

    status = run(task, controller, FakeLocator(None))

    assert status == "completed"
    assert ("type", "你好") in controller.events
    assert not any(e[0] == "click" for e in controller.events)


def test_find_type_with_template_clicks_then_types() -> None:
    start = Node(NodeKind.START, "开始")
    find = Node(
        NodeKind.FIND_TYPE,
        "输入",
        config={"templateData": png_data_url(), "text": "abc", "post_delay": 0},
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, find, stop], edges=[ex(start, "then", find), ex(find, "success", stop)])
    controller = FakeController()
    locator = FakeLocator(MatchResult(left=10, top=20, width=8, height=6, confidence=0.9))

    run(task, controller, locator)

    kinds = [e[0] for e in controller.events]
    assert kinds.index("click") < kinds.index("type")
    assert ("type", "abc") in controller.events


# --------------------------------------------------------------------------- #
# condition + branch
# --------------------------------------------------------------------------- #
def test_condition_branches_on_image_presence() -> None:
    def build() -> tuple[Task, FakeController]:
        start = Node(NodeKind.START, "开始")
        cond = Node(NodeKind.CONDITION, "看到了吗", config={"templateData": png_data_url()})
        yes = Node(NodeKind.TYPE_TEXT, "是", config={"text": "yes", "post_delay": 0})
        no = Node(NodeKind.TYPE_TEXT, "否", config={"text": "no", "post_delay": 0})
        stop = Node(NodeKind.STOP, "结束")
        task = Task(
            nodes=[start, cond, yes, no, stop],
            edges=[
                ex(start, "then", cond),
                ex(cond, "true", yes),
                ex(cond, "false", no),
                ex(yes, "then", stop),
                ex(no, "then", stop),
            ],
        )
        return task, FakeController()

    task, controller = build()
    run(task, controller, FakeLocator(MatchResult(0, 0, 4, 4, 0.9)))
    assert ("type", "yes") in controller.events
    assert ("type", "no") not in controller.events

    task, controller = build()
    run(task, controller, FakeLocator(None))
    assert ("type", "no") in controller.events
    assert ("type", "yes") not in controller.events


def test_branch_reads_bool_from_var_get() -> None:
    start = Node(NodeKind.START, "开始")
    setgo = Node(NodeKind.VAR_SET, "开", config={"name": "go", "value": True})
    getgo = Node(NodeKind.VAR_GET, "取 go", config={"name": "go"})
    branch = Node(NodeKind.BRANCH, "分支")
    yes = Node(NodeKind.TYPE_TEXT, "是", config={"text": "yes", "post_delay": 0})
    no = Node(NodeKind.TYPE_TEXT, "否", config={"text": "no", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        variables=[Variable(name="go", type="bool", default=False)],
        nodes=[start, setgo, getgo, branch, yes, no, stop],
        edges=[
            ex(start, "then", setgo),
            ex(setgo, "then", branch),
            data(getgo, "value", branch, "cond"),
            ex(branch, "true", yes),
            ex(branch, "false", no),
            ex(yes, "then", stop),
            ex(no, "then", stop),
        ],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(None))
    assert ("type", "yes") in controller.events
    assert ("type", "no") not in controller.events


def test_find_found_pin_flows_into_variable_then_branch() -> None:
    """find_click writes 找到 → var_set seen → var_get → branch routes 是/否."""
    start = Node(NodeKind.START, "开始")
    find = Node(NodeKind.FIND_CLICK, "找", config={"templateData": png_data_url(), "post_delay": 0})
    setseen = Node(NodeKind.VAR_SET, "存", config={"name": "seen"})
    getseen = Node(NodeKind.VAR_GET, "取", config={"name": "seen"})
    branch = Node(NodeKind.BRANCH, "分支")
    yes = Node(NodeKind.TYPE_TEXT, "是", config={"text": "yes", "post_delay": 0})
    no = Node(NodeKind.TYPE_TEXT, "否", config={"text": "no", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        variables=[Variable(name="seen", type="bool")],
        nodes=[start, find, setseen, getseen, branch, yes, no, stop],
        edges=[
            ex(start, "then", find),
            ex(find, "success", setseen),
            data(find, "found", setseen, "value"),
            ex(setseen, "then", branch),
            data(getseen, "value", branch, "cond"),
            ex(branch, "true", yes),
            ex(branch, "false", no),
            ex(yes, "then", stop),
            ex(no, "then", stop),
        ],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(MatchResult(0, 0, 4, 4, 0.9)))
    assert ("type", "yes") in controller.events
    assert ("type", "no") not in controller.events


def test_var_get_feeds_string_into_type_text() -> None:
    start = Node(NodeKind.START, "开始")
    getname = Node(NodeKind.VAR_GET, "取 name", config={"name": "name"})
    typer = Node(NodeKind.TYPE_TEXT, "输入", config={"text": "fallback", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        variables=[Variable(name="name", type="string", default="小明")],
        nodes=[start, getname, typer, stop],
        edges=[
            ex(start, "then", typer),
            data(getname, "value", typer, "text"),
            ex(typer, "then", stop),
        ],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(None))
    assert ("type", "小明") in controller.events


# --------------------------------------------------------------------------- #
# swipe
# --------------------------------------------------------------------------- #
def test_swipe_screen_points_scale_and_drag() -> None:
    start = Node(NodeKind.START, "开始")
    swipe = Node(
        NodeKind.SWIPE,
        "滑动",
        config={
            "shotW": 960,
            "shotH": 540,
            "points": [
                {"mode": "screen", "x": 10, "y": 20},
                {"mode": "screen", "x": 100, "y": 200},
                {"mode": "screen", "x": 300, "y": 400},
            ],
            "durations": [0.1, 0.2],
            "post_delay": 0,
        },
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, swipe, stop], edges=[ex(start, "then", swipe), ex(swipe, "success", stop)])
    controller = FakeController()  # screen 1920x1080 → 2x scale

    status = run(task, controller, FakeLocator(None))

    assert status == "completed"
    drags = [e for e in controller.events if e[0] == "drag"]
    assert drags == [("drag", [(20, 40), (200, 400), (600, 800)], [0.1, 0.2], "left")]


def test_swipe_image_point_locates_then_drags() -> None:
    start = Node(NodeKind.START, "开始")
    swipe = Node(
        NodeKind.SWIPE,
        "滑动",
        config={
            "shotW": 960,
            "shotH": 540,
            "points": [
                {"mode": "image", "template": png_data_url(), "threshold": 0.8, "offsetX": 0, "offsetY": 0},
                {"mode": "screen", "x": 100, "y": 200},
            ],
            "durations": [0.5],
            "post_delay": 0,
        },
    )
    stop = Node(NodeKind.STOP, "结束")
    task = Task(nodes=[start, swipe, stop], edges=[ex(start, "then", swipe), ex(swipe, "success", stop)])
    controller = FakeController()  # screen 1920x1080 → 2x scale
    locator = FakeLocator(MatchResult(left=40, top=50, width=20, height=20, confidence=0.95))

    status = run(task, controller, locator)  # image center (50, 60); screen (100,200)→(200,400)

    assert status == "completed"
    drags = [e for e in controller.events if e[0] == "drag"]
    assert drags == [("drag", [(50, 60), (200, 400)], [0.5], "left")]


def test_swipe_image_point_not_found_routes_fail() -> None:
    start = Node(NodeKind.START, "开始")
    swipe = Node(
        NodeKind.SWIPE,
        "滑动",
        config={
            "points": [
                {"mode": "image", "template": png_data_url()},
                {"mode": "screen", "x": 5, "y": 5},
            ],
            "post_delay": 0,
        },
    )
    failed = Node(NodeKind.TYPE_TEXT, "失败", config={"text": "miss", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, swipe, failed, stop],
        edges=[ex(start, "then", swipe), ex(swipe, "fail", failed), ex(failed, "then", stop)],
    )
    controller = FakeController()

    status = run(task, controller, FakeLocator(None))  # template never found

    assert status == "completed"
    assert not any(e[0] == "drag" for e in controller.events)
    assert ("type", "miss") in controller.events


def test_swipe_too_few_points_routes_fail() -> None:
    start = Node(NodeKind.START, "开始")
    swipe = Node(NodeKind.SWIPE, "滑动", config={"points": [{"mode": "screen", "x": 1, "y": 2}], "post_delay": 0})
    failed = Node(NodeKind.TYPE_TEXT, "失败", config={"text": "few", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, swipe, failed, stop],
        edges=[ex(start, "then", swipe), ex(swipe, "fail", failed), ex(failed, "then", stop)],
    )
    controller = FakeController()

    status = run(task, controller, FakeLocator(None))

    assert status == "completed"
    assert not any(e[0] == "drag" for e in controller.events)
    assert ("type", "few") in controller.events


# --------------------------------------------------------------------------- #
# trigger modes & loops
# --------------------------------------------------------------------------- #
def test_times_mode_runs_repeat_times() -> None:
    start = Node(NodeKind.START, "开始")
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.TIMES,
        repeat=3,
        nodes=[start, key, stop],
        edges=[ex(start, "then", key), ex(key, "then", stop)],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(None))
    assert sum(1 for e in controller.events if e[0] == "press") == 3


def test_loop_mode_stops_when_event_set() -> None:
    stop_event = threading.Event()

    class StoppingController(FakeController):
        def press(self, combo: str) -> None:
            super().press(combo)
            stop_event.set()  # stop after the first iteration

    start = Node(NodeKind.START, "开始")
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.LOOP,
        nodes=[start, key, stop],
        edges=[ex(start, "then", key), ex(key, "then", stop)],
    )
    controller = StoppingController()
    status = run_task(task, controller=controller, locator=FakeLocator(None), stop=stop_event)
    assert status == "stopped"
    assert sum(1 for e in controller.events if e[0] == "press") == 1


def test_loop_repeats_body_fixed_count() -> None:
    start = Node(NodeKind.START, "开始")
    loop = Node(NodeKind.LOOP, "循环", config={"count": 3})
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, loop, key, stop],
        edges=[
            ex(start, "then", loop),
            ex(loop, "body", key),
            ex(key, "then", loop),  # body loops back into the loop node
            ex(loop, "done", stop),
        ],
    )
    controller = FakeController()
    status = run(task, controller, FakeLocator(None))
    assert status == "completed"
    assert sum(1 for e in controller.events if e[0] == "press") == 3


def test_loop_while_image_respects_max_iterations() -> None:
    start = Node(NodeKind.START, "开始")
    loop = Node(
        NodeKind.LOOP_WHILE,
        "条件循环",
        config={"source": "image", "templateData": png_data_url(), "mode": "true", "max_iterations": 2},
    )
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        nodes=[start, loop, key, stop],
        edges=[
            ex(start, "then", loop),
            ex(loop, "body", key),
            ex(key, "then", loop),
            ex(loop, "done", stop),
        ],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(MatchResult(0, 0, 4, 4, 0.9)))
    assert sum(1 for e in controller.events if e[0] == "press") == 2


def test_loop_while_bool_input_stops_when_false() -> None:
    start = Node(NodeKind.START, "开始")
    getgo = Node(NodeKind.VAR_GET, "取 go", config={"name": "go"})
    loop = Node(NodeKind.LOOP_WHILE, "条件循环", config={"max_iterations": 50})
    flip = Node(NodeKind.VAR_SET, "关", config={"name": "go", "value": False})
    key = Node(NodeKind.KEY_PRESS, "按键", config={"keys": "a", "post_delay": 0})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        variables=[Variable(name="go", type="bool", default=True)],
        nodes=[start, getgo, loop, flip, key, stop],
        edges=[
            ex(start, "then", loop),
            data(getgo, "value", loop, "cond"),
            ex(loop, "body", flip),
            ex(flip, "then", key),
            ex(key, "then", loop),
            ex(loop, "done", stop),
        ],
    )
    controller = FakeController()
    run(task, controller, FakeLocator(None))
    assert sum(1 for e in controller.events if e[0] == "press") == 1


# --------------------------------------------------------------------------- #
# post-delay defaults
# --------------------------------------------------------------------------- #
def test_post_delay_defaults_per_kind() -> None:
    from flowpilot.engine.runner import _post_delay

    assert _post_delay(Node(NodeKind.KEY_PRESS, "k", config={"keys": "a"})) == 1.0
    assert _post_delay(Node(NodeKind.SWIPE, "s")) == 1.0
    assert _post_delay(Node(NodeKind.KEY_PRESS, "k", config={"post_delay": 0.3})) == 0.3
    assert _post_delay(Node(NodeKind.DELAY, "d")) == 0.0
    assert _post_delay(Node(NodeKind.CONDITION, "c")) == 0.0


# --------------------------------------------------------------------------- #
# persistence + legacy migration
# --------------------------------------------------------------------------- #
def test_store_round_trip_with_variables() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = TaskStore(Path(tmp))
        task = Task(
            name="存一下",
            hotkey="ctrl+alt+1",
            nodes=[Node(NodeKind.START, "开始")],
            variables=[Variable(name="seen", type="bool")],
        )
        store.save(task)

        loaded = store.get(task.id)
        assert loaded is not None
        assert loaded.name == "存一下"
        assert loaded.hotkey == "ctrl+alt+1"
        assert [v.name for v in loaded.variables] == ["seen"]
        assert store.delete(task.id) is True
        assert store.get(task.id) is None


def test_legacy_task_migrates_to_pin_model() -> None:
    raw = {
        "name": "旧任务",
        "nodes": [
            {"id": "s", "kind": "start", "title": "开始"},
            {"id": "f", "kind": "find_click", "title": "找", "config": {"templateData": "x"}},
            {"id": "sv", "kind": "set_var", "title": "设", "config": {"name": "go", "value": True}},
            {"id": "cv", "kind": "check_var", "title": "判", "config": {"name": "go"}},
            {"id": "e", "kind": "stop", "title": "结束"},
        ],
        "edges": [
            {"source": "s", "target": "f", "label": "next"},
            {"source": "f", "target": "sv", "label": "next"},
            {"source": "sv", "target": "cv", "label": "next"},
            {"source": "cv", "target": "e", "label": "true"},
        ],
    }
    task = Task.from_dict(raw)

    kinds = {n.id: n.kind for n in task.nodes}
    assert kinds["sv"] == NodeKind.VAR_SET
    assert kinds["cv"] == NodeKind.BRANCH

    handles = {(e.source, e.target): e.source_handle for e in task.edges}
    assert handles[("s", "f")] == "then"
    assert handles[("f", "sv")] == "success"  # find_click "next" → success
    assert handles[("sv", "cv")] == "then"
    assert handles[("cv", "e")] == "true"
    assert all(e.kind == "exec" for e in task.edges)

    assert any(v.name == "go" and v.type == "bool" for v in task.variables)


def test_swipe_then_edge_migrates_to_success() -> None:
    raw = {
        "nodes": [
            {"id": "s", "kind": "start", "title": "开始"},
            {"id": "w", "kind": "swipe", "title": "滑", "config": {"points": []}},
            {"id": "e", "kind": "stop", "title": "结束"},
        ],
        "edges": [
            {"source": "s", "source_handle": "then", "target": "w", "target_handle": "exec", "kind": "exec"},
            {"source": "w", "source_handle": "then", "target": "e", "target_handle": "exec", "kind": "exec"},
        ],
    }
    task = Task.from_dict(raw)
    handles = {(e.source, e.target): e.source_handle for e in task.edges}
    assert handles[("s", "w")] == "then"  # start still leaves via then
    assert handles[("w", "e")] == "success"  # swipe then → success


# --------------------------------------------------------------------------- #
# runtime manager + HTTP API
# --------------------------------------------------------------------------- #
def test_manager_run_then_stop(tmp_path) -> None:
    store = TaskStore(tmp_path)
    start = Node(NodeKind.START, "开始")
    delay = Node(NodeKind.DELAY, "等", config={"min_seconds": 0.05, "max_seconds": 0.05})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.LOOP,
        nodes=[start, delay, stop],
        edges=[ex(start, "then", delay), ex(delay, "then", stop)],
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


def test_run_ignores_retrigger_while_running(tmp_path) -> None:
    store = TaskStore(tmp_path)
    start = Node(NodeKind.START, "开始")
    delay = Node(NodeKind.DELAY, "等", config={"min_seconds": 0.2, "max_seconds": 0.2})
    stop = Node(NodeKind.STOP, "结束")
    task = Task(
        trigger_mode=TriggerMode.LOOP,
        nodes=[start, delay, stop],
        edges=[ex(start, "then", delay), ex(delay, "then", stop)],
    )
    store.save(task)
    runtime = EngineRuntime(store, locator=FakeLocator(None), controller=FakeController(),
                            binder=DummyBinder())

    runtime.run(task.id)
    first = runtime._threads[task.id]
    runtime.run(task.id)  # ignored while running: same thread, no restart
    assert runtime._threads[task.id] is first

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
    assert created["variables"] == []
    assert created["edges"][0]["source_handle"] == "then"

    listing = client.get("/api/tasks").json()
    assert any(item["id"] == task_id for item in listing)

    created["hotkey"] = "ctrl+alt+9"
    updated = client.put(f"/api/tasks/{task_id}", json=created).json()
    assert updated["hotkey"] == "ctrl+alt+9"

    assert client.post(f"/api/tasks/{task_id}/run").json()["ok"] is True
    assert client.post(f"/api/tasks/{task_id}/stop").json()["ok"] is True

    assert client.delete(f"/api/tasks/{task_id}").json()["ok"] is True
    assert client.get(f"/api/tasks/{task_id}").status_code == 404
