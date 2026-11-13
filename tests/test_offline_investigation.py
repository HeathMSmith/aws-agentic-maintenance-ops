
"""Regression tests for the offline maintenance investigation demo."""

import hashlib
import json

from pytest import CaptureFixture

from agent.bedrock.investigation_workflow import run_investigation_workflow
from examples.offline_bedrock_client import OfflineBedrockClient
from examples.run_offline_investigation import main


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

    records = result["investigation"]["evidence_records"]

    assert len(records) == 5
    assert {record["tool_name"] for record in records} == expected_tools

    for record in records:
        assert record["tool_use_id"]
        assert record["identifiers"]
        assert isinstance(record["result"], dict)
        assert len(record["sha256"]) == 64

        record_content = {
            key: value
            for key, value in record.items()
            if key != "sha256"
        }

        canonical_json = json.dumps(
            record_content,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

        expected_digest = hashlib.sha256(
            canonical_json.encode("utf-8")
        ).hexdigest()

        assert record["sha256"] == expected_digest

    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert (
        result["proposal"]["proposed_action"]
        == "request_equipment_shutdown"
    )

    policy = result["policy_result"]

    assert policy["status"] == "evaluated"
    assert policy["policy_decision"]["decision"] == "requires_approval"


def test_offline_investigation_output_identifies_unverified_explanation(capsys: CaptureFixture[str]):
    """Expose validated scheduling facts separately from model-generated text."""

    main()

    output = json.loads(capsys.readouterr().out)

    assert output["workflow_status"] == "evaluated"

    assert output["operational_facts"] == {
        "asset_id": "CONV-MTR-042",
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "maintenance_window_available": False,
    }
    assert output["maintenance_window_assessment"] == {
        "available": False,
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "summary": (
            "No active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        ),
    }
    assert output["investigation_text_status"] == "model_generated_unverified"
    assert output["proposal_reason_status"] == "model_generated_unverified"
    assert output["authorization_assessment"] == {
        "action": "request_equipment_shutdown",
        "decision": "requires_approval",
        "summary": (
            "The proposed equipment shutdown requires approval "
            "before execution."
        ),
    }
    assert output["proposal"]["proposed_action"] == "request_equipment_shutdown"
    assert output["policy_decision"]["decision"] == "requires_approval"

    assert output["decision_summary"] == {
        "maintenance_window_assessment": output[
            "maintenance_window_assessment"
        ],
        "authorization_assessment": output[
            "authorization_assessment"
        ],
    }

    assert "investigation" not in output["decision_summary"]
    assert "proposal" not in output["decision_summary"]
