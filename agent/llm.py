import json

import anthropic

from agent import fake_llm
from agent.config import SETTINGS
from agent.mcp_client import call_tool, list_read_tools, mcp_session

MAX_TURNS = 6

INVESTIGATE_PROMPT = """You are an SRE agent investigating a Kubernetes incident.
You have read-only tools for pods, events, logs, deployments, Helm history and Prometheus.
Use them to collect evidence, usually 3 to 6 calls is enough.
When you are confident about the root cause, call submit_diagnosis.
Don't guess. If the evidence is unclear, say so and set confidence to low.
Image tags are git commit SHAs, and the pod annotations deploy/git-sha, deploy/actor and
deploy/github-run-url show which commit and CI run shipped the version. Quote them if a bad
deploy is the cause. Compare the failing Helm revision with the last healthy one and name the
revision to roll back to."""

PROPOSE_PROMPT = """You are an SRE agent proposing exactly one fix for a Kubernetes incident.
A human will review it before it runs. Pick the least destructive fix that solves the root cause
(for example, a bad deploy should be rolled back, not hand patched).
Always fill in real params like namespace and deployment or release name.
If no action is clearly safe, use action no_action and explain why."""

DIAGNOSIS_TOOL = {
    "name": "submit_diagnosis",
    "description": "Submit your final root-cause diagnosis once you have enough evidence.",
    "input_schema": {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string", "description": "One or two sentence root cause."},
            "evidence": {"type": "array", "items": {"type": "string"}, "description": "Log lines, events, metric values."},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "affected_resources": {"type": "array", "items": {"type": "string"}, "description": "e.g. deployment/checkout-service"},
        },
        "required": ["root_cause", "evidence", "confidence", "affected_resources"],
    },
}

FIX_TOOL = {
    "name": "submit_remediation_plan",
    "description": "Submit exactly one fix for a human to approve.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["rollout_restart", "scale_deployment", "rollback_deployment", "helm_rollback", "patch_resource", "no_action"],
            },
            "params": {
                "type": "object",
                "description": (
                    "Keys per action:\n"
                    "  rollout_restart:     {namespace, deployment}\n"
                    "  scale_deployment:    {namespace, deployment, replicas}\n"
                    "  rollback_deployment: {namespace, deployment, to_revision?}\n"
                    "  helm_rollback:       {namespace, release, revision?}\n"
                    "  patch_resource:      {namespace, resource_type, name, patch_json}\n"
                    "  no_action:           {}"
                ),
            },
            "rationale": {"type": "string"},
            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "expected_outcome": {"type": "string"},
        },
        "required": ["action", "params", "rationale", "risk_level", "expected_outcome"],
    },
}


def new_client():
    return anthropic.AsyncAnthropic(api_key=SETTINGS.anthropic_api_key)


async def ask_claude(client, system, tools, messages):
    return await client.messages.create(
        model=SETTINGS.anthropic_model,
        max_tokens=2048,
        system=system,
        tools=tools,
        tool_choice={"type": "auto"},
        messages=messages,
    )


async def run_diagnosis(namespace, hint):
    if not SETTINGS.anthropic_api_key:
        return fake_llm.TRANSCRIPT, fake_llm.diagnose()

    client = new_client()
    transcript = []
    messages = [{
        "role": "user",
        "content": f"Investigate namespace '{namespace}'. Alert hint: {hint or 'none, general health check'}",
    }]

    async with mcp_session() as session:
        tools = await list_read_tools(session) + [DIAGNOSIS_TOOL]

        for turn in range(MAX_TURNS + 1):
            # on the last turn only allow submit_diagnosis so it has to answer
            last_turn = turn == MAX_TURNS
            if last_turn:
                messages.append({"role": "user", "content": "Out of time. Call submit_diagnosis now."})

            resp = await ask_claude(client, INVESTIGATE_PROMPT, [DIAGNOSIS_TOOL] if last_turn else tools, messages)
            messages.append({"role": "assistant", "content": resp.content})

            for block in resp.content:
                if block.type == "text":
                    transcript.append(block.text)

            calls = [b for b in resp.content if b.type == "tool_use"]
            for call in calls:
                if call.name == "submit_diagnosis":
                    return "\n".join(transcript), call.input

            if not calls:
                messages.append({"role": "user", "content": "Please call submit_diagnosis now."})
                continue

            results = []
            for call in calls:
                output = await call_tool(session, call.name, call.input)
                transcript.append(f"-> {call.name}({json.dumps(call.input)})\n   {output[:2000]}")
                results.append({"type": "tool_result", "tool_use_id": call.id, "content": output[:4000]})
            messages.append({"role": "user", "content": results})

    return "\n".join(transcript), fake_llm.diagnose()


async def propose_fix(diagnosis):
    if not SETTINGS.anthropic_api_key:
        return fake_llm.propose()

    client = new_client()
    messages = [{
        "role": "user",
        "content": f"Diagnosis:\n{json.dumps(diagnosis, indent=2)}\n\nCall submit_remediation_plan with your plan.",
    }]

    # retry a couple of times in case Claude answers in plain text
    for _ in range(3):
        resp = await ask_claude(client, PROPOSE_PROMPT, [FIX_TOOL], messages)
        for block in resp.content:
            if block.type == "tool_use":
                return block.input
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": "Please call submit_remediation_plan now."})

    raise RuntimeError("Claude didn't return a fix after 3 tries")
