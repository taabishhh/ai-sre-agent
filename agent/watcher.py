import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from agent.tools import kubectl_tool

# container states that mean a pod is broken
BAD_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
    "InvalidImageName",
    "RunContainerError",
}


@dataclass
class Issue:
    pod: str
    container: str
    reason: str
    detail: str = ""

    def describe(self):
        where = f"{self.pod}/{self.container}" if self.container else self.pod
        extra = f" ({self.detail})" if self.detail else ""
        return f"{where}: {self.reason}{extra}"


def parse_time(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def seconds_since(value, now):
    t = parse_time(value)
    return (now - t).total_seconds() if t else 0


def container_issues(pod_name, status):
    issues = []
    containers = status.get("initContainerStatuses", []) + status.get("containerStatuses", [])
    for c in containers:
        waiting = (c.get("state") or {}).get("waiting") or {}
        last_exit = (c.get("lastState") or {}).get("terminated") or {}

        if waiting.get("reason") in BAD_REASONS:
            issues.append(Issue(pod_name, c.get("name", ""), waiting["reason"], (waiting.get("message") or "")[:120]))
        elif last_exit.get("reason") == "OOMKilled" and not c.get("ready"):
            issues.append(Issue(pod_name, c.get("name", ""), "OOMKilled", f"restarts={c.get('restartCount', 0)}"))
    return issues


def detect_issues(pods_json, now=None, grace_s=90):
    # grace_s gives new pods time to start before we call them broken
    now = now or datetime.now(timezone.utc)
    issues = []

    for pod in pods_json.get("items", []):
        meta = pod.get("metadata", {})
        status = pod.get("status", {})
        name = meta.get("name", "?")
        phase = status.get("phase", "")

        if meta.get("deletionTimestamp") or phase == "Succeeded":
            continue

        found = container_issues(name, status)
        if found:
            issues += found
            continue

        conditions = {c.get("type"): c for c in status.get("conditions", [])}
        scheduled = conditions.get("PodScheduled", {})
        ready = conditions.get("Ready", {})

        if phase == "Failed":
            issues.append(Issue(name, "", status.get("reason") or "Failed", (status.get("message") or "")[:120]))
        elif phase == "Pending" and scheduled.get("status") == "False":
            if seconds_since(meta.get("creationTimestamp"), now) > grace_s:
                issues.append(Issue(name, "", scheduled.get("reason", "Unschedulable"), (scheduled.get("message") or "")[:120]))
        elif phase == "Running" and ready.get("status") == "False":
            if seconds_since(ready.get("lastTransitionTime"), now) > grace_s:
                issues.append(Issue(name, "", "NotReady", "running but failing readiness checks"))

    return issues


def build_hint(namespace, issues):
    listed = "; ".join(i.describe() for i in issues[:6])
    more = f" (+{len(issues) - 6} more)" if len(issues) > 6 else ""
    return (
        f"Watcher found {len(issues)} unhealthy pod problem(s) in namespace '{namespace}': "
        f"{listed}{more}. A deployment may have just happened."
    )


async def watch(
    namespace,
    interval_s=20,
    cooldown_s=600,
    settle_s=15,
    max_runs=None,
    max_polls=None,
    get_pods=kubectl_tool.get_pods_json,
    run_graph=None,
    sleep=asyncio.sleep,
    clock=time.monotonic,
):
    # run the agent once per incident, not on every poll
    # it can run again once things are healthy, or after cooldown_s if still broken
    if run_graph is None:
        from agent import graph
        run_graph = graph.run

    ready_to_run = True
    last_run = float("-inf")
    runs = 0
    polls = 0

    print(f"[watch] watching namespace '{namespace}' every {interval_s:g}s. Ctrl+C to stop.")
    while True:
        polls += 1
        try:
            issues = detect_issues(await asyncio.to_thread(get_pods, namespace))
        except Exception as e:
            print(f"[watch] could not read pods: {e}")
            issues = None

        if issues == []:
            if not ready_to_run:
                print("[watch] namespace is healthy again.")
            ready_to_run = True

        elif issues and (ready_to_run or clock() - last_run > cooldown_s):
            print(f"\n[watch] PROBLEM DETECTED in '{namespace}':")
            for issue in issues:
                print(f"[watch]   - {issue.describe()}")
            print(f"[watch] waiting {settle_s:g}s, then starting the agent...")
            await sleep(settle_s)

            ready_to_run = False
            last_run = clock()
            runs += 1
            await run_graph(namespace, build_hint(namespace, issues))
            print(f"\n[watch] agent finished. Back to watching '{namespace}'.")
            if max_runs and runs >= max_runs:
                return runs

        if max_polls and polls >= max_polls:
            return runs
        await sleep(interval_s)
