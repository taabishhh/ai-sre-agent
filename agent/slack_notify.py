import os
import time

import requests

from agent.config import SETTINGS


def save_to_disk(summary):
    os.makedirs("runs", exist_ok=True)
    path = f"runs/{int(time.time())}-summary.md"
    with open(path, "w") as f:
        f.write(summary)
    return path


def post_summary(summary):
    path = save_to_disk(summary)

    if not SETTINGS.slack_webhook_url:
        return f"No Slack webhook set, summary saved to {path}"

    # slack cuts off long messages, so keep it under the limit
    payload = {"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": summary[:2900]}}]}
    try:
        resp = requests.post(SETTINGS.slack_webhook_url, json=payload, timeout=10)
        if resp.ok:
            return f"Posted to Slack, also saved to {path}"
        return f"Slack returned {resp.status_code}, summary saved to {path}"
    except Exception as e:
        return f"Slack post failed ({type(e).__name__}), summary saved to {path}"
