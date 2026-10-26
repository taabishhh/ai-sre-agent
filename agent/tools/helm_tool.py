from agent.config import SETTINGS
from agent.tools import mock_data
from agent.tools.shell import check_namespace, run


def helm(*args):
    return run(["helm", *args])


def list_releases(namespace):
    if SETTINGS.mock_mode:
        return mock_data.HELM_LIST
    return helm("list", "-n", namespace)


def get_release_status(namespace, release):
    if SETTINGS.mock_mode:
        return mock_data.HELM_STATUS
    return helm("status", release, "-n", namespace)


def get_release_history(namespace, release):
    if SETTINGS.mock_mode:
        return mock_data.HELM_HISTORY
    return helm("history", release, "-n", namespace)


def rollback_release(namespace, release, revision=0):
    check_namespace(namespace)
    if SETTINGS.mock_mode:
        return f"[MOCK] release '{release}' rolled back to revision {revision or 'previous'} in {namespace}"
    args = ["rollback", release]
    if revision:
        args.append(str(revision))
    return helm(*args, "-n", namespace)
