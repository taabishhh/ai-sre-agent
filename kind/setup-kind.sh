#!/usr/bin/env bash
# creates a free local cluster with kind
set -euo pipefail

CLUSTER_NAME="ai-sre-demo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v kind >/dev/null 2>&1 || { echo "kind is not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is not installed or not running"; exit 1; }

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "kind cluster '${CLUSTER_NAME}' already exists. Reusing it."
else
  echo "Creating kind cluster '${CLUSTER_NAME}'..."
  kind create cluster --config "${SCRIPT_DIR}/kind-config.yaml"
fi

kubectl create namespace demo --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "Cluster ready. kubectl context set to 'kind-${CLUSTER_NAME}'."
echo "Next: ../k8s-manifests/install-prometheus.sh   (installs Prometheus + Grafana)"
echo "Then: ../demo/inject_chaos.sh                   (breaks something on purpose)"
