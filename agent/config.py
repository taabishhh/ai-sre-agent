import os

from dotenv import load_dotenv

load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self):
        self.mock_mode = env_bool("MOCK_MODE")
        self.auto_approve = env_bool("AUTO_APPROVE")

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        self.default_namespace = os.getenv("DEFAULT_NAMESPACE", "default")
        self.kubectl_timeout_s = int(os.getenv("KUBECTL_TIMEOUT_S", "20"))
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        # the agent can only change things in these namespaces
        namespaces = os.getenv("ALLOWED_NAMESPACES", "default,demo").split(",")
        self.allowed_namespaces = [ns.strip() for ns in namespaces if ns.strip()]
        self.max_replica_scale = int(os.getenv("MAX_REPLICA_SCALE", "10"))


SETTINGS = Settings()
