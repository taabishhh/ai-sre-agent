import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_args():
    p = argparse.ArgumentParser(description="AI SRE agent for Kubernetes")
    p.add_argument("--namespace", default=os.getenv("DEFAULT_NAMESPACE", "demo"))
    p.add_argument("--hint", default="", help="what the alert said, e.g. 'checkout-service 5xx spike'")
    p.add_argument("--mock", action="store_true", help="use fake cluster data, no real cluster needed")
    p.add_argument("--watch", action="store_true", help="keep watching and run the agent when pods break")
    p.add_argument("--interval", type=float, default=20, help="seconds between checks in watch mode")
    p.add_argument("--cooldown", type=float, default=600, help="seconds before re-running for the same problem")
    p.add_argument("--auto-approve", action="store_true", help="skip the approval step (demo only)")
    return p.parse_args()


def main():
    args = parse_args()
    if args.mock:
        os.environ["MOCK_MODE"] = "true"
    if args.auto_approve:
        os.environ["AUTO_APPROVE"] = "true"

    # import after setting env vars, config reads them on import
    from agent import graph, watcher
    from agent.config import SETTINGS

    print("=" * 60)
    print("AI SRE Agent")
    print(f"  namespace:     {args.namespace}")
    print(f"  mock mode:     {SETTINGS.mock_mode}")
    print(f"  auto approve:  {SETTINGS.auto_approve}")
    print(f"  claude:        {'on' if SETTINGS.anthropic_api_key else 'off (no API key, using demo answers)'}")
    print(f"  allowed ns:    {', '.join(SETTINGS.allowed_namespaces)}")
    print("=" * 60)

    if args.watch:
        try:
            asyncio.run(watcher.watch(args.namespace, interval_s=args.interval, cooldown_s=args.cooldown))
        except KeyboardInterrupt:
            print("\n[watch] stopped.")
        return

    result = asyncio.run(graph.run(args.namespace, args.hint))
    took = result.get("finished_at", 0) - result.get("started_at", 0)
    print(f"\nDone in {took:.1f}s. status={result.get('approval_status')} executed={result.get('executed', False)}")


if __name__ == "__main__":
    main()
