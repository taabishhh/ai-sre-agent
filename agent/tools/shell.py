import subprocess

from agent.config import SETTINGS


def run(cmd):
    # runs a CLI command and returns its output as text, errors included
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=SETTINGS.kubectl_timeout_s)
    except FileNotFoundError:
        return f"ERROR: {cmd[0]} is not installed"
    except subprocess.TimeoutExpired:
        return f"ERROR: `{' '.join(cmd)}` timed out"

    if proc.returncode != 0:
        return f"ERROR running `{' '.join(cmd)}`:\n{proc.stderr.strip()}"
    return proc.stdout.strip()


def check_namespace(namespace):
    if namespace not in SETTINGS.allowed_namespaces:
        allowed = ", ".join(SETTINGS.allowed_namespaces)
        raise PermissionError(f"Namespace '{namespace}' is not allowed (allowed: {allowed})")
