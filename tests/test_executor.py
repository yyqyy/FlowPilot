from flowpilot.executor import WorkflowExecutor
from flowpilot.model import Edge, Node, NodeKind, Workflow
from flowpilot.screen import MatchResult


def test_dry_run_follows_edges_without_sleeping() -> None:
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Wait", config={"min_seconds": 60, "max_seconds": 60})
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(nodes=[start, delay, stop], edges=[Edge(start.id, delay.id), Edge(delay.id, stop.id)])
    output: list[str] = []

    WorkflowExecutor(workflow, dry_run=True, log=output.append).run()

    assert output[-1] == "Workflow completed."
    assert "Delay 60.00s" in output


class FakeMatcher:
    def find_template(self, template_path, *, threshold):
        assert str(template_path) == "button.png"
        assert threshold == 0.9
        return MatchResult(10, 20, 30, 40, 0.95)


def test_find_image_records_match_for_following_nodes() -> None:
    start = Node(NodeKind.START, "Start")
    find = Node(
        NodeKind.FIND_IMAGE,
        "Find button",
        config={"template": "button.png", "threshold": 0.9},
    )
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(nodes=[start, find, stop], edges=[Edge(start.id, find.id), Edge(find.id, stop.id)])
    output: list[str] = []
    executor = WorkflowExecutor(workflow, dry_run=True, log=output.append, screen_matcher=FakeMatcher())

    executor.run()

    assert executor.last_match is not None
    assert executor.last_match.center == (25, 40)
    assert "Found image at (25, 40) (95.0% confidence)" in output
