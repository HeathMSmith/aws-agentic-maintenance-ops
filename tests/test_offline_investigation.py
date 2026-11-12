
"""Regression tests for the offline maintenance investigation demo."""

from agent.bedrock.investigation_workflow import run_investigation_workflow
from examples.offline_bedrock_client import OfflineBedrockClient


def test_offline_investigation_requires_approval():
    """The scripted shutdown proposal must require human approval."""

    client = OfflineBedrockClient()

    result = run_investigation_workflow(
        client=client,
        model_id="offline-demo",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "evaluated"
    assert len(client.calls) == 3

    expected_tools = {
        "get_equipment_alert",
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }

    trace = result["investigation"]["execution_trace"]

    assert len(trace) == 5
    assert {entry["tool_name"] for entry in trace} == expected_tools
    assert all(entry["status"] == "success" for entry in trace)

    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert (
        result["proposal"]["proposed_action"]
        == "request_equipment_shutdown"
    )

    policy = result["policy_result"]

    assert policy["status"] == "evaluated"
    assert policy["policy_decision"]["decision"] == "requires_approval"
