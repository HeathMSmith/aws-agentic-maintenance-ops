import pytest

from agent.bedrock.evidence_completeness import (
    REQUIRED_EVIDENCE_TOOLS,
    validate_evidence_completeness,
)


def make_complete_trace():
    return [
        {"tool_name": name, "status": "success"}
        for name in sorted(REQUIRED_EVIDENCE_TOOLS)
    ]


def test_complete_evidence_trace():
    result = validate_evidence_completeness(make_complete_trace())

    assert result == {
        "valid": True,
        "completed_tools": sorted(REQUIRED_EVIDENCE_TOOLS),
    }


@pytest.mark.parametrize(
    "missing_tool",
    sorted(REQUIRED_EVIDENCE_TOOLS),
)
def test_missing_required_tool(missing_tool):
    trace = [
        entry
        for entry in make_complete_trace()
        if entry["tool_name"] != missing_tool
    ]

    result = validate_evidence_completeness(trace)

    assert result == {
        "valid": False,
        "reason": "required evidence tools were not completed",
        "missing_tools": [missing_tool],
    }


def test_failed_tool_does_not_count_as_complete():
    trace = make_complete_trace()

    for entry in trace:
        if entry["tool_name"] == "get_equipment_alert":
            entry["status"] = "error"

    result = validate_evidence_completeness(trace)

    assert result["valid"] is False
    assert result["missing_tools"] == ["get_equipment_alert"]


@pytest.mark.parametrize(
    "trace",
    [
        None,
        {},
        "invalid",
        123,
    ],
)
def test_invalid_trace_type_rejected(trace):
    result = validate_evidence_completeness(trace)

    assert result == {
        "valid": False,
        "reason": "execution trace must be a list",
    }


def test_empty_trace_reports_all_required_tools():
    result = validate_evidence_completeness([])

    assert result["valid"] is False
    assert result["missing_tools"] == sorted(REQUIRED_EVIDENCE_TOOLS)


def test_malformed_trace_entries_do_not_count():
    trace = make_complete_trace()

    trace = [
        entry
        for entry in trace
        if entry["tool_name"] != "get_asset_context"
    ]

    trace.extend([
        None,
        "invalid",
        {},
        {"tool_name": "get_asset_context"},
        {"tool_name": 123, "status": "success"},
    ])

    result = validate_evidence_completeness(trace)

    assert result["valid"] is False
    assert result["missing_tools"] == ["get_asset_context"]


def test_duplicate_successful_calls_are_accepted():
    trace = make_complete_trace()

    trace.append({
        "tool_name": "get_equipment_alert",
        "status": "success",
    })

    result = validate_evidence_completeness(trace)

    assert result["valid"] is True


def test_failed_call_followed_by_success_is_accepted():
    trace = make_complete_trace()

    trace.insert(0, {
        "tool_name": "get_equipment_alert",
        "status": "error",
    })

    result = validate_evidence_completeness(trace)

    assert result["valid"] is True


def test_optional_policy_tool_is_not_required():
    trace = make_complete_trace()

    trace.append({
        "tool_name": "evaluate_proposed_maintenance_action",
        "status": "success",
    })

    result = validate_evidence_completeness(trace)

    assert result["valid"] is True
    assert "evaluate_proposed_maintenance_action" not in (
        result["completed_tools"]
    )
