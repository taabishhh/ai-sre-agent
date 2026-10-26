# watcher tests, no cluster needed
import os

os.environ["MOCK_MODE"] = "true"
os.environ["ANTHROPIC_API_KEY"] = ""

import asyncio
from datetime import datetime, timezone

from agent import watcher

NOW = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)


def pod(name, phase="Running", containers=None, conditions=None, created="2026-10-09T11:00:00Z"):
    return {
        "metadata": {"name": name, "creationTimestamp": created},
        "status": {"phase": phase, "containerStatuses": containers or [], "conditions": conditions or []},
    }


def container(name="app", ready=True, waiting=None, last_terminated=None, restarts=0):
    return {
        "name": name,
        "ready": ready,
        "restartCount": restarts,
        "state": {"waiting": {"reason": waiting}} if waiting else {"running": {}},
        "lastState": {"terminated": {"reason": last_terminated}} if last_terminated else {},
    }


def test_healthy_pod_has_no_issues():
    p = pod("a", containers=[container()], conditions=[{"type": "Ready", "status": "True"}])
    assert watcher.detect_issues({"items": [p]}, now=NOW) == []


def test_crashloop_detected():
    p = pod("a", containers=[container(ready=False, waiting="CrashLoopBackOff", restarts=5)])
    issues = watcher.detect_issues({"items": [p]}, now=NOW)
    assert [i.reason for i in issues] == ["CrashLoopBackOff"]


def test_image_pull_error_detected():
    p = pod("a", phase="Pending", containers=[container(ready=False, waiting="ImagePullBackOff")])
    assert watcher.detect_issues({"items": [p]}, now=NOW)[0].reason == "ImagePullBackOff"


def test_oomkilled_detected():
    p = pod("a", containers=[container(ready=False, last_terminated="OOMKilled", restarts=3)])
    assert watcher.detect_issues({"items": [p]}, now=NOW)[0].reason == "OOMKilled"


def test_not_ready_only_flagged_after_grace_period():
    cond = lambda ts: [{"type": "Ready", "status": "False", "lastTransitionTime": ts}]
    fresh = pod("fresh", containers=[container(ready=False)], conditions=cond("2026-10-09T11:59:30Z"))
    stuck = pod("stuck", containers=[container(ready=False)], conditions=cond("2026-10-09T11:50:00Z"))
    issues = watcher.detect_issues({"items": [fresh, stuck]}, now=NOW)
    assert [i.pod for i in issues] == ["stuck"]
    assert issues[0].reason == "NotReady"


def test_terminating_and_finished_pods_ignored():
    gone = pod("gone", containers=[container(ready=False, waiting="CrashLoopBackOff")])
    gone["metadata"]["deletionTimestamp"] = "2026-10-09T11:59:00Z"
    done = pod("done", phase="Succeeded")
    assert watcher.detect_issues({"items": [gone, done]}, now=NOW) == []


def test_mock_fixture_is_flagged():
    from agent.tools import mock_data

    issues = watcher.detect_issues(mock_data.PODS, now=NOW)
    assert len(issues) == 2 and all(i.reason == "CrashLoopBackOff" for i in issues)


def _run_watch(pod_sequence, **kwargs):
    # feed watch() a list of pod snapshots and count how often the agent runs
    calls = []
    snapshots = iter(pod_sequence)
    last = {}

    def get_pods(ns):
        nonlocal last
        last = next(snapshots, last)
        return last

    async def run_graph(ns, hint):
        calls.append(hint)

    async def no_sleep(_):
        return None

    ticks = iter(range(0, 10_000, 10))
    runs = asyncio.run(
        watcher.watch(
            "demo",
            get_pods=get_pods,
            run_graph=run_graph,
            sleep=no_sleep,
            clock=lambda: next(ticks),
            max_polls=len(pod_sequence),
            **kwargs,
        )
    )
    return runs, calls


BAD = {"items": [pod("a", containers=[container(ready=False, waiting="CrashLoopBackOff")])]}
GOOD = {"items": [pod("a", containers=[container()], conditions=[{"type": "Ready", "status": "True"}])]}


def test_agent_starts_once_per_incident():
    runs, calls = _run_watch([GOOD, BAD, BAD, BAD], cooldown_s=10_000)
    assert runs == 1 and "CrashLoopBackOff" in calls[0]


def test_agent_starts_again_after_recovery():
    runs, _ = _run_watch([BAD, GOOD, BAD], cooldown_s=10_000)
    assert runs == 2


def test_kubectl_errors_do_not_crash_the_watcher():
    def broken(ns):
        raise RuntimeError("connection refused")

    async def no_sleep(_):
        return None

    runs = asyncio.run(watcher.watch("demo", get_pods=broken, sleep=no_sleep, max_polls=3))
    assert runs == 0
