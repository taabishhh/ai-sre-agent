import json
import subprocess

from agent.config import SETTINGS
from agent.tools import mock_data
from agent.tools.shell import check_namespace, run


def kubectl(*args):
    return run(["kubectl", *args])


def get_pods(namespace):
    if SETTINGS.mock_mode:
        return mock_data.pods_table()
    return kubectl("get", "pods", "-n", namespace, "-o", "wide")


def describe_pod(namespace, pod):
    if SETTINGS.mock_mode:
        return mock_data.DESCRIBE_POD
    return kubectl("describe", "pod", pod, "-n", namespace)


def get_logs(namespace, pod, container="", tail_lines=200):
    if SETTINGS.mock_mode:
        return mock_data.LOGS
    args = ["logs", pod, "-n", namespace, f"--tail={tail_lines}"]
    if container:
        args += ["-c", container]
    return kubectl(*args)


def get_events(namespace):
    if SETTINGS.mock_mode:
        return mock_data.EVENTS
    return kubectl("get", "events", "-n", namespace, "--sort-by=.lastTimestamp")


def get_deployments(namespace):
    if SETTINGS.mock_mode:
        return mock_data.DEPLOYMENTS
    return kubectl("get", "deployments", "-n", namespace)


def get_pods_json(namespace):
    # used by the watcher, raises if kubectl fails
    if SETTINGS.mock_mode:
        return mock_data.PODS
    proc = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
        capture_output=True, text=True, timeout=SETTINGS.kubectl_timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "kubectl failed")
    return json.loads(proc.stdout)


def rollout_restart(namespace, deployment):
    check_namespace(namespace)
    if SETTINGS.mock_mode:
        return f"[MOCK] deployment/{deployment} restarted in {namespace}"
    return kubectl("rollout", "restart", f"deployment/{deployment}", "-n", namespace)


def scale_deployment(namespace, deployment, replicas):
    check_namespace(namespace)
    if replicas < 0 or replicas > SETTINGS.max_replica_scale:
        return f"REFUSED: {replicas} replicas is over the limit of {SETTINGS.max_replica_scale}"
    if SETTINGS.mock_mode:
        return f"[MOCK] deployment/{deployment} scaled to {replicas} in {namespace}"
    return kubectl("scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace)


def rollback_deployment(namespace, deployment, to_revision=0):
    check_namespace(namespace)
    if SETTINGS.mock_mode:
        return f"[MOCK] deployment/{deployment} rolled back in {namespace}"
    args = ["rollout", "undo", f"deployment/{deployment}", "-n", namespace]
    if to_revision:
        args.append(f"--to-revision={to_revision}")
    return kubectl(*args)


def patch_resource(namespace, resource_type, name, patch_json):
    check_namespace(namespace)
    if SETTINGS.mock_mode:
        return f"[MOCK] {resource_type}/{name} patched in {namespace}: {patch_json}"
    return kubectl("patch", resource_type, name, "-n", namespace, "--type=merge", "-p", patch_json)
