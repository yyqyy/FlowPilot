from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from flowpilot.engine.manager import EngineRuntime
from flowpilot.engine.model import Edge, Node, NodeKind, Task, summarize
from flowpilot.engine.store import TaskStore


def _starter_task(name: str) -> Task:
    start = Node(NodeKind.START, "开始", 80, 200)
    stop = Node(NodeKind.STOP, "结束", 520, 200)
    edge = Edge(source=start.id, source_handle="then", target=stop.id, target_handle="exec")
    return Task(name=name, nodes=[start, stop], edges=[edge])


def web_dist() -> Path:
    return Path(__file__).resolve().parents[3] / "web" / "dist"


def create_app(runtime: EngineRuntime) -> FastAPI:
    app = FastAPI(title="FlowPilot Engine")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    store = runtime.store

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return {
            "running": runtime.running_ids(),
            "hotkeys": runtime.binder.available,
            "log": runtime.recent_log(),
        }

    @app.get("/api/tasks")
    def list_tasks() -> list[dict[str, Any]]:
        return [summarize(t) for t in store.list()]

    @app.post("/api/tasks")
    def create_task(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        task = _starter_task(str(payload.get("name", "新任务")))
        store.save(task)
        runtime.refresh_hotkeys()
        return task.to_dict()

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str) -> dict[str, Any]:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="task not found")
        return task.to_dict()

    @app.put("/api/tasks/{task_id}")
    def update_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if store.get(task_id) is None:
            raise HTTPException(status_code=404, detail="task not found")
        payload["id"] = task_id
        task = Task.from_dict(payload)
        store.save(task)
        runtime.refresh_hotkeys()
        return task.to_dict()

    @app.delete("/api/tasks/{task_id}")
    def delete_task(task_id: str) -> dict[str, Any]:
        runtime.stop(task_id)
        ok = store.delete(task_id)
        runtime.refresh_hotkeys()
        if not ok:
            raise HTTPException(status_code=404, detail="task not found")
        return {"ok": True}

    @app.post("/api/tasks/{task_id}/run")
    def run_task_endpoint(task_id: str) -> dict[str, Any]:
        try:
            runtime.run(task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc
        return {"ok": True, "running": True}

    @app.post("/api/tasks/{task_id}/stop")
    def stop_task_endpoint(task_id: str) -> dict[str, Any]:
        runtime.stop(task_id)
        return {"ok": True}

    @app.post("/api/stop")
    def stop_all_endpoint() -> dict[str, Any]:
        runtime.stop_all()
        return {"ok": True}

    dist = web_dist()
    if (dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(dist / "index.html")
    else:

        @app.get("/")
        def index_missing() -> HTMLResponse:
            return HTMLResponse(
                "<h1>FlowPilot</h1><p>网页界面尚未构建。请在 <code>web/</code> 下运行 "
                "<code>npm install &amp;&amp; npm run build</code>，或直接运行 "
                "<code>start.ps1</code>。</p>",
                status_code=200,
            )

    return app


def build_runtime() -> EngineRuntime:
    return EngineRuntime(TaskStore())
