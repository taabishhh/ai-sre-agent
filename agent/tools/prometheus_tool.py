import time

import requests

from agent.config import SETTINGS
from agent.tools import mock_data


def prom_get(path, params):
    try:
        resp = requests.get(SETTINGS.prometheus_url + path, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def format_result(payload):
    # turns prometheus json into short lines like {pod="x"} => 14
    if payload.get("status") != "success":
        return f"Prometheus error: {payload.get('error')}"
    series_list = payload["data"]["result"]
    if not series_list:
        return "No data returned."

    lines = []
    for series in series_list:
        labels = ", ".join(f'{k}="{v}"' for k, v in series["metric"].items())
        value = series["value"][1] if "value" in series else series["values"][-1][1]
        lines.append(f"{{{labels}}} => {value}")
    return "\n".join(lines)


def query(promql):
    if SETTINGS.mock_mode:
        if "http_requests" in promql or "error" in promql.lower():
            return format_result(mock_data.PROM_ERROR_RATE)
        return format_result(mock_data.PROM_RESTART_COUNT)
    return format_result(prom_get("/api/v1/query", {"query": promql}))


def query_range(promql, minutes=20):
    if SETTINGS.mock_mode:
        return format_result(mock_data.PROM_RANGE_RESTARTS)
    end = time.time()
    params = {"query": promql, "start": end - minutes * 60, "end": end, "step": 60}
    return format_result(prom_get("/api/v1/query_range", params))


def pod_restart_counts(namespace):
    return query(f'sum(increase(kube_pod_container_status_restarts_total{{namespace="{namespace}"}}[1h])) by (pod)')


def service_error_rate(namespace):
    errors = f'sum(rate(http_requests_total{{namespace="{namespace}",status=~"5.."}}[5m])) by (service)'
    total = f'sum(rate(http_requests_total{{namespace="{namespace}"}}[5m])) by (service)'
    return query(f"{errors} / {total}")
