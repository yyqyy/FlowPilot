from __future__ import annotations

import json
import os
from pathlib import Path

from flowpilot.engine.model import Task


def default_data_dir() -> Path:
    """Per-user location where tasks are auto-saved."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "FlowPilot" / "tasks"


class TaskStore:
    """Loads and saves tasks as one JSON file per task. No manual export needed."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or default_data_dir()
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        safe = "".join(c for c in task_id if c.isalnum() or c in "-_")
        return self.directory / f"{safe}.json"

    def list(self) -> list[Task]:
        tasks: list[Task] = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                tasks.append(Task.from_dict(raw))
            except (OSError, ValueError, KeyError):
                continue
        return tasks

    def get(self, task_id: str) -> Task | None:
        path = self._path(task_id)
        if not path.exists():
            return None
        try:
            return Task.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError):
            return None

    def save(self, task: Task) -> Task:
        path = self._path(task.id)
        path.write_text(
            json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return task

    def delete(self, task_id: str) -> bool:
        path = self._path(task_id)
        if path.exists():
            path.unlink()
            return True
        return False
