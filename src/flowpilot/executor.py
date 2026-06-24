from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import random
import time

from flowpilot.model import Node, NodeKind, Workflow
from flowpilot.screen import MatchResult, ScreenMatcher


LogSink = Callable[[str], None]


class WorkflowExecutor:
    """Small sequential executor; real input is opt-in, dry-run is the default."""

    def __init__(
        self,
        workflow: Workflow,
        *,
        dry_run: bool = True,
        log: LogSink = print,
        screen_matcher: ScreenMatcher | None = None,
    ):
        self.workflow = workflow
        self.dry_run = dry_run
        self.log = log
        self.screen_matcher = screen_matcher or ScreenMatcher()
        self.last_match: MatchResult | None = None
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
        if node.kind == NodeKind.FIND_IMAGE:
            template_value = str(node.config.get("template", "")).strip()
            if not template_value:
                raise ValueError(f"{node.title} needs a template image.")
            template = Path(template_value)
            threshold = float(node.config.get("threshold", 0.85))
            self.last_match = self.screen_matcher.find_template(template, threshold=threshold)
            if self.last_match is None:
                raise RuntimeError(f"Image not found: {template}")
            self.log(
                f"Found image at {self.last_match.center} "
                f"({self.last_match.confidence:.1%} confidence)"
            )
            return
        if self.dry_run:
            self.log(f"DRY RUN: {node.config}")
            return
        import pyautogui

        pyautogui.FAILSAFE = True
        if node.kind == NodeKind.CLICK:
            if node.config.get("target") == "last_match":
                if self.last_match is None:
                    raise RuntimeError("Click requires a successful image match.")
                x, y = self.last_match.center
            else:
                x, y = int(node.config["x"]), int(node.config["y"])
            pyautogui.click(x, y)
        elif node.kind == NodeKind.TYPE_TEXT:
            pyautogui.write(str(node.config.get("text", "")), interval=0.03)
