# runs the whole loop with fake data, no cluster or API key needed
import os

os.environ["MOCK_MODE"] = "true"
os.environ["AUTO_APPROVE"] = "true"
os.environ["ALLOWED_NAMESPACES"] = "demo"
os.environ["ANTHROPIC_API_KEY"] = ""

import asyncio

import pytest

from agent import graph


@pytest.mark.asyncio
async def test_full_loop_mock_mode():
    final_state = await graph.run("demo", "checkout-service alerting: elevated 5xx / pods restarting")

    assert final_state["diagnosis"]["confidence"] == "high"
    assert "checkout-service" in final_state["diagnosis"]["root_cause"] or "DATABASE_DSN" in final_state["diagnosis"]["root_cause"]

    assert final_state["proposal"]["action"] == "helm_rollback"

    assert final_state["approval_status"] == "auto_approved"
    assert final_state["executed"] is True
    assert "[MOCK]" in final_state["execution_result"]

    assert "Incident Summary" in final_state["summary_markdown"]


def test_full_loop_mock_mode_sync_entrypoint():
    final_state = asyncio.run(graph.run("demo", "checkout-service alerting"))
    assert final_state["executed"] is True
