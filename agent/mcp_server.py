from mcp.server.mcpserver import MCPServer

from agent.tools import helm_tool, kubectl_tool, prometheus_tool

# exposes kubectl, helm and prometheus as MCP tools
# you can also plug this into Claude Desktop: python -m agent.mcp_server

mcp = MCPServer("ai-sre-cluster-tools")


# read tools, safe for the AI to call on its own

@mcp.tool()
def k8s_get_pods(namespace: str = "default") -> str:
    """List pods in a namespace with status, restart counts, and readiness."""
    return kubectl_tool.get_pods(namespace)


@mcp.tool()
def k8s_describe_pod(namespace: str, pod: str) -> str:
    """Full `kubectl describe pod` output: recent events, container states, exit codes."""
    return kubectl_tool.describe_pod(namespace, pod)


@mcp.tool()
def k8s_get_logs(namespace: str, pod: str, container: str = "", tail_lines: int = 200) -> str:
    """Recent container logs for a pod."""
    return kubectl_tool.get_logs(namespace, pod, container, tail_lines)


@mcp.tool()
def k8s_get_events(namespace: str = "default") -> str:
    """Recent Kubernetes events in a namespace (probe failures, back-offs, scheduling issues)."""
    return kubectl_tool.get_events(namespace)


@mcp.tool()
def k8s_get_deployments(namespace: str = "default") -> str:
    """Deployment rollout status: desired vs ready vs available replicas."""
    return kubectl_tool.get_deployments(namespace)


@mcp.tool()
def helm_list_releases(namespace: str = "default") -> str:
    """List Helm releases in a namespace with status and revision."""
    return helm_tool.list_releases(namespace)


@mcp.tool()
def helm_get_release_status(namespace: str, release: str) -> str:
    """Full `helm status` for a release: chart/app version, notes."""
    return helm_tool.get_release_status(namespace, release)


@mcp.tool()
def helm_get_release_history(namespace: str, release: str) -> str:
    """Revision history for a Helm release, to match an incident with a deploy."""
    return helm_tool.get_release_history(namespace, release)


@mcp.tool()
def prom_query(promql: str) -> str:
    """Run an instant PromQL query against Prometheus."""
    return prometheus_tool.query(promql)


@mcp.tool()
def prom_query_range(promql: str, minutes: int = 20) -> str:
    """Run a PromQL range query over the last N minutes."""
    return prometheus_tool.query_range(promql, minutes)


@mcp.tool()
def prom_pod_restart_counts(namespace: str = "default") -> str:
    """Restart count per pod in a namespace over the last hour."""
    return prometheus_tool.pod_restart_counts(namespace)


@mcp.tool()
def prom_service_error_rate(namespace: str = "default") -> str:
    """5xx error rate per service in a namespace over the last 5 minutes."""
    return prometheus_tool.service_error_rate(namespace)


# write tools, only run after a human says yes

@mcp.tool()
def k8s_rollout_restart(namespace: str, deployment: str) -> str:
    """Restart all pods of a Deployment. Needs human approval."""
    return kubectl_tool.rollout_restart(namespace, deployment)


@mcp.tool()
def k8s_scale_deployment(namespace: str, deployment: str, replicas: int) -> str:
    """Scale a Deployment to N replicas. Needs human approval."""
    return kubectl_tool.scale_deployment(namespace, deployment, replicas)


@mcp.tool()
def k8s_rollback_deployment(namespace: str, deployment: str, to_revision: int = 0) -> str:
    """Undo the last (or a specific) rollout of a Deployment. Needs human approval."""
    return kubectl_tool.rollback_deployment(namespace, deployment, to_revision)


@mcp.tool()
def k8s_patch_resource(namespace: str, resource_type: str, name: str, patch_json: str) -> str:
    """Apply a JSON merge patch to a resource. Needs human approval."""
    return kubectl_tool.patch_resource(namespace, resource_type, name, patch_json)


@mcp.tool()
def helm_rollback_release(namespace: str, release: str, revision: int = 0) -> str:
    """Roll a Helm release back to the previous (or a specific) revision. Needs human approval."""
    return helm_tool.rollback_release(namespace, release, revision)


READ_TOOLS = {
    "k8s_get_pods",
    "k8s_describe_pod",
    "k8s_get_logs",
    "k8s_get_events",
    "k8s_get_deployments",
    "helm_list_releases",
    "helm_get_release_status",
    "helm_get_release_history",
    "prom_query",
    "prom_query_range",
    "prom_pod_restart_counts",
    "prom_service_error_rate",
}


if __name__ == "__main__":
    mcp.run(transport="stdio")
