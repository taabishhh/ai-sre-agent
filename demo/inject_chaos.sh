#!/usr/bin/env bash
# deploys a healthy checkout-service, then a broken one with a typo in the database host
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${1:-demo}"
CHART="${SCRIPT_DIR}/helm/checkout-service"

command -v helm >/dev/null 2>&1 || { echo "helm is not installed"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is not installed"; exit 1; }

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Deploying the good version (v46)..."
helm upgrade --install checkout-service "${CHART}" -n "${NAMESPACE}" \
  -f "${SCRIPT_DIR}/values-good.yaml" --wait --timeout 90s

sleep 15

# no --wait here, this one is supposed to fail
echo "==> Deploying the bad version (v47)..."
helm upgrade --install checkout-service "${CHART}" -n "${NAMESPACE}" \
  -f "${SCRIPT_DIR}/values-bad.yaml"

echo ""
echo "Done. Pods should start crash-looping in about a minute."
echo "Then run: python scripts/run_agent.py --namespace ${NAMESPACE}"
