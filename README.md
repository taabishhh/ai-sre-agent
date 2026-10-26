# AI SRE Agent

An AI agent that finds out why something broke in a Kubernetes cluster and suggests a fix.

When pods start failing, the agent looks at the pods, logs, events, Helm history and Prometheus metrics, works out the root cause, and proposes one fix (like rolling back a bad deploy). Nothing changes until a human types `y`. After that it applies the fix and posts a short report to Slack.

Built with Python, LangGraph, Claude, MCP, kubectl, Helm, Prometheus and Terraform (EKS).

## How it works

The agent runs in 5 steps:

1. **Diagnose**: Claude calls read-only tools (get pods, read logs, check Helm history, query Prometheus) until it knows the root cause.
2. **Propose**: Claude picks one fix from a fixed list (restart, scale, rollback, Helm rollback, patch).
3. **Approve**: The fix is shown in the terminal and you answer y/n.
4. **Execute**: If you said yes, the fix runs.
5. **Summarize**: A report is saved to `runs/` and posted to Slack if a webhook is set.

```
diagnose -> propose -> approve -> execute -> summarize
                          |                    ^
                          +---- denied --------+
```

The kubectl/Helm/Prometheus tools live in an MCP server (`agent/mcp_server.py`). The agent talks to it like any other MCP client, so you could also plug the same server into Claude Desktop.

There's also a **watch mode** that checks the namespace every 20 seconds and starts the agent on its own when pods go into states like `CrashLoopBackOff`, `ImagePullBackOff` or `OOMKilled`.

### Safety

- The AI only gets read-only tools. It can't change anything by itself.
- Changes only run after a human approves.
- Changes are only allowed in namespaces listed in `ALLOWED_NAMESPACES`.
- Scaling is capped by `MAX_REPLICA_SCALE`.

## Project structure

```
agent/
  graph.py          the 5 steps wired together with LangGraph
  llm.py            Claude calls for diagnosing and proposing a fix
  fake_llm.py       canned answers used when there's no API key
  approval.py       the y/n prompt
  report.py         builds the markdown report
  slack_notify.py   saves the report and sends it to Slack
  watcher.py        watch mode, spots unhealthy pods
  mcp_server.py     exposes kubectl, helm and prometheus as MCP tools
  mcp_client.py     connects the agent to the MCP server
  config.py         settings from .env
  state.py          data passed between steps
  tools/            kubectl, helm and prometheus wrappers + fake data
scripts/run_agent.py   start here
tests/                 tests that run without a cluster
demo/                  a small Helm chart and a script that breaks it on purpose
kind/                  free local cluster setup
k8s-manifests/         Prometheus + Grafana install
terraform/             EKS cluster on AWS
docs/CICD_DEMO.md      full demo with GitHub Actions and EKS
```

## Try it (no cluster or API key needed)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_agent.py --mock
```

This uses fake cluster data: a bad Helm deploy with a typo in the database host, so the pods keep crashing. Type `y` when asked and it "rolls back" the release. Without an API key it uses canned answers so you can see the whole flow. Add `ANTHROPIC_API_KEY` to `.env` to use real Claude.

Run the tests:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Run it on a real cluster

You'll need Docker, kubectl, Helm and kind (or an AWS account for EKS).

```bash
./kind/setup-kind.sh                     # local cluster (or see terraform/README.md for EKS)
./k8s-manifests/install-prometheus.sh    # metrics
./demo/inject_chaos.sh demo              # break something on purpose

cp .env.example .env                     # add your ANTHROPIC_API_KEY
python scripts/run_agent.py --namespace demo --hint "checkout-service pods restarting"
```

Or let it watch and react by itself:

```bash
python scripts/run_agent.py --watch --namespace demo
```

For Slack, create an Incoming Webhook in a Slack app and put the URL in `SLACK_WEBHOOK_URL`.

## Settings

All settings are in `.env` (see `.env.example`):

| Name | What it does |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key. Without it, canned answers are used |
| `MOCK_MODE` | `true` uses fake cluster data |
| `AUTO_APPROVE` | `true` skips the y/n step. Demo only |
| `ALLOWED_NAMESPACES` | namespaces the agent is allowed to change |
| `MAX_REPLICA_SCALE` | highest replica count it can scale to |
| `PROMETHEUS_URL` | where Prometheus is running |
| `SLACK_WEBHOOK_URL` | optional Slack webhook |
