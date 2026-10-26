# fake cluster data for --mock mode
# story: a bad helm deploy (v47) has a typo in the database host, so pods crash-loop

import time

NOW = int(time.time())

PODS = {
    "items": [
        {
            "metadata": {"name": "checkout-service-7f9c8d6b5-abcde", "namespace": "demo"},
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "checkout-service",
                        "ready": False,
                        "restartCount": 14,
                        "state": {
                            "waiting": {
                                "reason": "CrashLoopBackOff",
                                "message": "back-off 5m0s restarting failed container=checkout-service",
                            }
                        },
                        "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/checkout-service:v47",
                    }
                ],
            },
        },
        {
            "metadata": {"name": "checkout-service-7f9c8d6b5-fghij", "namespace": "demo"},
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "checkout-service",
                        "ready": False,
                        "restartCount": 12,
                        "state": {
                            "waiting": {
                                "reason": "CrashLoopBackOff",
                                "message": "back-off 5m0s restarting failed container=checkout-service",
                            }
                        },
                        "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/checkout-service:v47",
                    }
                ],
            },
        },
        {
            "metadata": {"name": "checkout-service-6c5b8d9f4-zzzzz", "namespace": "demo"},
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "checkout-service",
                        "ready": True,
                        "restartCount": 0,
                        "state": {"running": {"startedAt": "2026-09-17T10:00:00Z"}},
                        "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/checkout-service:v46",
                    }
                ],
            },
        },
    ]
}

DESCRIBE_POD = """Name:         checkout-service-7f9c8d6b5-abcde
Namespace:    demo
Node:         ip-10-0-3-142.ec2.internal
Status:       Running
IP:           10.0.3.91
Controlled By:  ReplicaSet/checkout-service-7f9c8d6b5
Containers:
  checkout-service:
    Image:          123456789012.dkr.ecr.us-east-1.amazonaws.com/checkout-service:v47
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
    Ready:          False
    Restart Count:  14
Events:
  Type     Reason     Age                From     Message
  ----     ------     ----               ----     -------
  Warning  BackOff    2m (x40 over 20m)  kubelet  Back-off restarting failed container
  Warning  Unhealthy  2m (x14 over 18m)  kubelet  Readiness probe failed: connection refused
"""

LOGS = """2026-09-18T04:10:01Z INFO  starting checkout-service v47
2026-09-18T04:10:01Z INFO  loading config from env
2026-09-18T04:10:01Z FATAL failed to connect to database: dial tcp: lookup postgress-primary.demo.svc.cluster.local: no such host
2026-09-18T04:10:01Z FATAL  DATABASE_DSN env var appears misconfigured (host "postgress-primary", expected "postgres-primary")
2026-09-18T04:10:01Z INFO  shutting down
"""

EVENTS = """LAST SEEN   TYPE      REASON              OBJECT                                    MESSAGE
3m          Warning   BackOff             pod/checkout-service-7f9c8d6b5-abcde      Back-off restarting failed container
3m          Warning   BackOff             pod/checkout-service-7f9c8d6b5-fghij      Back-off restarting failed container
20m         Normal    ScalingReplicaSet   deployment/checkout-service                Scaled up replica set checkout-service-7f9c8d6b5 to 2
20m         Normal    SuccessfulCreate    replicaset/checkout-service-7f9c8d6b5      Created pod: checkout-service-7f9c8d6b5-abcde
18m         Warning   Unhealthy           pod/checkout-service-7f9c8d6b5-abcde      Readiness probe failed: connection refused
"""

DEPLOYMENTS = """NAME               READY   UP-TO-DATE   AVAILABLE   AGE
checkout-service   1/3     2            1           4h12m
"""

HELM_LIST = """NAME              NAMESPACE   REVISION   UPDATED                                 STATUS     CHART                   APP VERSION
checkout-service  demo        7          2026-09-18 04:09:52.221 UTC             deployed   checkout-service-1.7.0  v47
"""

HELM_STATUS = """NAME: checkout-service
LAST DEPLOYED: Thu Sep 18 04:09:52 2026
NAMESPACE: demo
STATUS: deployed
REVISION: 7
NOTES:
checkout-service v47 deployed. DATABASE_DSN overridden in values-prod.yaml revision 7
(previous revision 6 used DATABASE_DSN pointing at "postgres-primary", revision 7 introduced
a typo: "postgress-primary").
"""

HELM_HISTORY = """REVISION  UPDATED                   STATUS       CHART                   APP VERSION  DESCRIPTION
5         2026-09-15 09:00:00 UTC  superseded   checkout-service-1.6.0  v45          Upgrade complete
6         2026-09-17 10:00:00 UTC  superseded   checkout-service-1.6.1  v46          Upgrade complete
7         2026-09-18 04:09:52 UTC  deployed     checkout-service-1.7.0  v47          Upgrade complete
"""

PROM_RESTART_COUNT = {
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"pod": "checkout-service-7f9c8d6b5-abcde", "namespace": "demo"},
                "value": [NOW, "14"],
            },
            {
                "metric": {"pod": "checkout-service-7f9c8d6b5-fghij", "namespace": "demo"},
                "value": [NOW, "12"],
            },
        ],
    },
}

PROM_ERROR_RATE = {
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"service": "checkout-service", "namespace": "demo"},
                "value": [NOW, "0.97"],
            }
        ],
    },
}

PROM_RANGE_RESTARTS = {
    "status": "success",
    "data": {
        "resultType": "matrix",
        "result": [
            {
                "metric": {"pod": "checkout-service-7f9c8d6b5-abcde", "namespace": "demo"},
                "values": [
                    [NOW - 1200, "0"],
                    [NOW - 900, "2"],
                    [NOW - 600, "6"],
                    [NOW - 300, "10"],
                    [NOW, "14"],
                ],
            }
        ],
    },
}


def pods_table():
    lines = ["NAME                                   READY   STATUS             RESTARTS   AGE"]
    for pod in PODS["items"]:
        c = pod["status"]["containerStatuses"][0]
        ready = "1/1" if c["ready"] else "0/1"
        status = c["state"].get("waiting", {}).get("reason") or "Running"
        lines.append(f"{pod['metadata']['name']:<38} {ready:<7} {status:<18} {c['restartCount']:<10} 4h")
    return "\n".join(lines)
