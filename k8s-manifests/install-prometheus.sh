#!/usr/bin/env bash
# installs prometheus + grafana so the agent has metrics to look at
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${MONITORING_NAMESPACE:-monitoring}"

command -v helm >/dev/null 2>&1 || { echo "helm is not installed."; exit 1; }

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install kube-prom-stack prometheus-community/kube-prometheus-stack \
  --namespace "${NAMESPACE}" \
  -f "${SCRIPT_DIR}/prometheus-values.yaml" \
  --wait --timeout 5m

echo ""
echo "Prometheus + Grafana installed in namespace '${NAMESPACE}'."
echo ""
echo "Port-forward Prometheus (agent's PROMETHEUS_URL target):"
echo "  kubectl -n ${NAMESPACE} port-forward svc/kube-prom-stack-kube-prome-prometheus 9090:9090"
echo ""
echo "Port-forward Grafana (default admin / prom-operator):"
echo "  kubectl -n ${NAMESPACE} port-forward svc/kube-prom-stack-grafana 3000:80"
