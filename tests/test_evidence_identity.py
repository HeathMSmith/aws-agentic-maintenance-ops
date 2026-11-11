import pytest

from agent.bedrock.evidence_identity import (
    validate_evidence_identity,
)


def make_valid_trace():
    tools = [
        ("get_equipment_alert", {"alert_id": "ALERT-0001"}),
        ("get_asset_context", {"asset_id": "CONV-MTR-042"}),
        ("get_maintenance_history", {"asset_id": "CONV-MTR-042"}),
        ("get_production_schedule", {"asset_id": "CONV-MTR-042"}),
        ("get_maintenance_window_status", {"asset_id": "CONV-MTR-042"}),
    ]

    return [
        {
            "model_call": 1,
            "tool_name": name,
            "status": "success",
            "identifiers": identifiers,
        }
        for name, identifiers in tools
    ]


def test_valid_evidence_identity():
    result = validate_evidence_identity(
        make_valid_trace(), "ALERT-0001"
    )

    assert result == {
        "valid": True,
        "alert_id": "ALERT-0001",
        "asset_id": "CONV-MTR-042",
    }


@pytest.mark.parametrize(
    "tool_name",
    [
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    ],
)
def test_rejects_wrong_asset_identifier(tool_name):
    trace = make_valid_trace()

    for entry in trace:
        if entry["tool_name"] == tool_name:
            entry["identifiers"] = {
                "asset_id": "CONV-MTR-999"
            }

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is False
    assert result["missing_or_mismatched_tools"] == [tool_name]


def test_rejects_wrong_alert_identifier():
    trace = make_valid_trace()
    trace[0]["identifiers"] = {"alert_id": "ALERT-9999"}

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is False
    assert result["missing_or_mismatched_tools"] == [
        "get_equipment_alert"
    ]


def test_rejects_unknown_requested_alert():
    result = validate_evidence_identity(
        make_valid_trace(), "ALERT-9999"
    )

    assert result == {
        "valid": False,
        "reason": "requested alert was not found",
    }


@pytest.mark.parametrize("alert_id", ["", "   ", None, 123])
def test_rejects_invalid_alert_id(alert_id):
    result = validate_evidence_identity(
        make_valid_trace(), alert_id
    )

    assert result["valid"] is False
    assert result["reason"] == (
        "alert_id must be a non-empty string"
    )


@pytest.mark.parametrize("trace", [None, {}, "invalid", 123])
def test_rejects_invalid_trace(trace):
    result = validate_evidence_identity(
        trace, "ALERT-0001"
    )

    assert result == {
        "valid": False,
        "reason": "execution trace must be a list",
    }


def test_failed_tool_execution_does_not_count():
    trace = make_valid_trace()
    trace[1]["status"] = "error"

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is False
    assert result["missing_or_mismatched_tools"] == [
        "get_asset_context"
    ]


def test_missing_identifiers_do_not_count():
    trace = make_valid_trace()
    trace[1]["identifiers"] = {}

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is False
    assert result["missing_or_mismatched_tools"] == [
        "get_asset_context"
    ]


def test_malformed_trace_entries_are_ignored():
    trace = make_valid_trace()
    trace.extend([None, "invalid", {}, {"status": "success"}])

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is True


def test_correct_retry_satisfies_identity_requirement():
    trace = make_valid_trace()

    trace.insert(
        0,
        {
            "model_call": 1,
            "tool_name": "get_asset_context",
            "status": "success",
            "identifiers": {
                "asset_id": "CONV-MTR-999"
            },
        },
    )

    result = validate_evidence_identity(trace, "ALERT-0001")

    assert result["valid"] is True
