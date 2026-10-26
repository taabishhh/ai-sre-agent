import time

from langgraph.graph import END, START, StateGraph

from agent import approval, llm, mcp_client, report, slack_notify
from agent.state import AgentState

# flow: diagnose -> propose -> approve -> execute -> summarize
# if the fix is denied we skip execute and go straight to summarize

# the only write tools the agent is allowed to run
ACTION_TO_TOOL = {
    "rollout_restart": "k8s_rollout_restart",
    "scale_deployment": "k8s_scale_deployment",
    "rollback_deployment": "k8s_rollback_deployment",
    "helm_rollback": "helm_rollback_release",
    "patch_resource": "k8s_patch_resource",
}


async def diagnose(state):
    print(f"\n[diagnose] investigating namespace '{state['namespace']}'...")
    transcript, diagnosis = await llm.run_diagnosis(state["namespace"], state.get("incident_hint", ""))
    print(f"[diagnose] root cause ({diagnosis['confidence']} confidence): {diagnosis['root_cause']}")
    return {"telemetry_transcript": transcript, "diagnosis": diagnosis}


async def propose(state):
    print("[propose] drafting a fix...")
    proposal = await llm.propose_fix(state["diagnosis"])
    print(f"[propose] action='{proposal['action']}' risk={proposal['risk_level']}")
    return {"proposal": proposal}


async def approve(state):
    status, note = approval.ask_for_approval(state["diagnosis"], state["proposal"])
    return {"approval_status": status, "approver_note": note}


def after_approval(state):
    approved = state["approval_status"] in ("approved", "auto_approved")
    has_action = state["proposal"]["action"] != "no_action"
    return "execute" if approved and has_action else "summarize"


async def execute(state):
    proposal = state["proposal"]
    tool = ACTION_TO_TOOL.get(proposal["action"])
    if not tool:
        return {"execution_result": f"Unknown action '{proposal['action']}'", "executed": False}

    print(f"[execute] calling {tool}({proposal['params']}) ...")
    result = await mcp_client.call_write_tool(tool, proposal["params"])
    print(f"[execute] result: {result}")
    return {"execution_result": result, "executed": True}


async def summarize(state):
    summary = report.format_summary(
        diagnosis=state["diagnosis"],
        proposal=state["proposal"],
        approval_status=state["approval_status"],
        execution_result=state.get("execution_result", ""),
        namespace=state["namespace"],
    )
    where = slack_notify.post_summary(summary)
    print("\n" + summary)
    print(f"[summarize] {where}")
    return {"summary_markdown": summary, "finished_at": time.time()}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("diagnose", diagnose)
    graph.add_node("propose", propose)
    graph.add_node("approve", approve)
    graph.add_node("execute", execute)
    graph.add_node("summarize", summarize)

    graph.add_edge(START, "diagnose")
    graph.add_edge("diagnose", "propose")
    graph.add_edge("propose", "approve")
    graph.add_conditional_edges("approve", after_approval, ["execute", "summarize"])
    graph.add_edge("execute", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


async def run(namespace, incident_hint=""):
    app = build_graph()
    start = {
        "namespace": namespace,
        "incident_hint": incident_hint,
        "approval_status": "pending",
        "started_at": time.time(),
    }
    return await app.ainvoke(start)
