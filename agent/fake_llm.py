# canned answers used when there's no ANTHROPIC_API_KEY
# they match the story in tools/mock_data.py

TRANSCRIPT = """[no API key, using canned demo answers]
1. k8s_get_pods -> 2/3 checkout-service pods in CrashLoopBackOff, 12-14 restarts
2. k8s_describe_pod -> exit code 1, BackOff events
3. k8s_get_logs -> FATAL lookup postgress-primary: no such host, DATABASE_DSN misconfigured
4. helm_get_release_history -> revision 7 deployed 4 min before the first crash, revision 6 was healthy
5. prom_pod_restart_counts -> restarts went from 0 to 14 in 20 minutes
"""


def diagnose():
    return {
        "root_cause": (
            "Helm release 'checkout-service' revision 7 has a typo in DATABASE_DSN "
            "('postgress-primary' instead of 'postgres-primary'), so every pod fails "
            "DNS lookup on startup and crash-loops."
        ),
        "evidence": [
            "Pod logs show: 'lookup postgress-primary.demo.svc.cluster.local: no such host'",
            "2/3 checkout-service pods in CrashLoopBackOff with 12-14 restarts",
            "Helm history shows revision 7 deployed ~4 minutes before the first BackOff event",
            "Prometheus restart count climbs from 0 to 14 starting right at the revision 7 deploy",
            "Revision 6 (previous, healthy) used the correct DSN host",
        ],
        "confidence": "high",
        "affected_resources": ["deployment/checkout-service", "helm release/checkout-service (namespace demo)"],
    }


def propose():
    return {
        "action": "helm_rollback",
        "params": {"namespace": "demo", "release": "checkout-service", "revision": 6},
        "rationale": (
            "The problem is a config typo shipped in Helm revision 7. Rolling back to revision 6, "
            "the last good one, is the fastest safe fix. A restart alone won't help because the "
            "new pods would still get the bad DSN."
        ),
        "risk_level": "low",
        "expected_outcome": (
            "Pods go back to v46 with the correct DATABASE_DSN, readiness checks pass, restarts stop "
            "and the 5xx error rate goes back to normal within 1-2 minutes."
        ),
    }
