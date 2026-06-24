from __future__ import annotations

from collections.abc import Callable
import random
import time

from flowpilot.model import Node, NodeKind, Workflow


LogSink = Callable[[str], None]


class WorkflowExecutor:
    """Small sequential executor; real input is opt-in, dry-run is the default."""

    def __init__(self, workflow: Workflow, *, dry_run: bool = True, log: LogSink = print):
        self.workflow = workflow
        self.dry_run = dry_run
        self.log = log
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        errors = self.workflow.validate()
        if errors:
            raise ValueError(" ".join(errors))
        nodes = {node.id: node for node in self.workflow.nodes}
        current = next(node for node in self.workflow.nodes if node.kind == NodeKind.START)
        visited = 0
        while not self._stopped:
            self._execute(current)
            visited += 1
            if visited > 10_000:
                raise RuntimeError("Execution limit reached; possible infinite workflow.")
            targets = [edge.target for edge in self.workflow.edges if edge.source == current.id]
            if not targets or current.kind == NodeKind.STOP:
                break
            current = nodes[targets[0]]
        self.log("Workflow stopped." if self._stopped else "Workflow completed.")

    def _execute(self, node: Node) -> None:
        self.log(f"[{node.kind}] {node.title}")
        if node.kind in {NodeKind.START, NodeKind.STOP}:
            return
        if node.kind == NodeKind.DELAY:
            low = float(node.config.get("min_seconds", 0.5))
            high = float(node.config.get("max_seconds", low))
            delay = random.uniform(min(low, high), max(low, high))
            self.log(f"Delay {delay:.2f}s")
            if not self.dry_run:
                time.sleep(delay)
            return
        if self.dry_run:
            self.log(f"DRY RUN: {node.config}")
            return
        import pyautogui

        pyautogui.FAILSAFE = True
        if node.kind == NodeKind.CLICK:
            pyautogui.click(int(node.config["x"]), int(node.config["y"]))
        elif node.kind == NodeKind.TYPE_TEXT:
            pyautogui.write(str(node.config.get("text", "")), interval=0.03)
        elif node.kind == NodeKind.FIND_IMAGE:
            self.log("Image matching backend will be enabled in milestone 0.2.")

