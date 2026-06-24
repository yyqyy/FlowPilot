from flowpilot.executor import WorkflowExecutor
from flowpilot.model import Edge, Node, NodeKind, Workflow


def test_dry_run_follows_edges_without_sleeping() -> None:
    start = Node(NodeKind.START, "Start")
    delay = Node(NodeKind.DELAY, "Wait", config={"min_seconds": 60, "max_seconds": 60})
    stop = Node(NodeKind.STOP, "Stop")
    workflow = Workflow(nodes=[start, delay, stop], edges=[Edge(start.id, delay.id), Edge(delay.id, stop.id)])
    output: list[str] = []

    WorkflowExecutor(workflow, dry_run=True, log=output.append).run()

    assert output[-1] == "Workflow completed."
    assert "Delay 60.00s" in output
