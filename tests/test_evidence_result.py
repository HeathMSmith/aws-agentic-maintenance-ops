import pytest

from agent.bedrock.evidence_result import validate_evidence_result


@pytest.mark.parametrize(
    "tool_name,identifier_field",
    [
        ("get_equipment_alert", "alert_id"),
        ("get_asset_context", "asset_id"),
        ("get_maintenance_history", "asset_id"),
        ("get_production_schedule", "asset_id"),
        ("get_maintenance_window_status", "asset_id"),
    ],
)
def test_accepts_matching_evidence_identifier(tool_name, identifier_field):
    identifier = (
        "ALERT-0001"
        if identifier_field == "alert_id"
        else "CONV-MTR-042"
    )

    result = validate_evidence_result(
        tool_name,
        {identifier_field: identifier},
        {identifier_field: identifier},
    )

    assert result == {"valid": True}


@pytest.mark.parametrize(
    "tool_name,identifier_field",
    [
        ("get_equipment_alert", "alert_id"),
        ("get_asset_context", "asset_id"),
        ("get_maintenance_history", "asset_id"),
        ("get_production_schedule", "asset_id"),
        ("get_maintenance_window_status", "asset_id"),
    ],
)
def test_rejects_mismatched_evidence_identifier(tool_name, identifier_field):
    requested_id = (
        "ALERT-0001"
        if identifier_field == "alert_id"
        else "CONV-MTR-042"
    )

    result = validate_evidence_result(
        tool_name,
        {identifier_field: requested_id},
        {identifier_field: "WRONG-ID"},
    )

    assert result == {
        "valid": False,
        "reason": "evidence result identifier mismatch",
    }


@pytest.mark.parametrize("tool_input", [None, [], "invalid", 123])
def test_rejects_invalid_tool_input(tool_input):
    result = validate_evidence_result(
        "get_asset_context",
        tool_input,
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "valid": False,
        "reason": "tool input must be a dictionary",
    }


@pytest.mark.parametrize("tool_result", [None, [], "invalid", 123])
def test_rejects_invalid_tool_result(tool_result):
    result = validate_evidence_result(
        "get_asset_context",
        {"asset_id": "CONV-MTR-042"},
        tool_result,
    )

    assert result == {
        "valid": False,
        "reason": "tool result must be a dictionary",
    }


def test_rejects_explicit_tool_error():
    result = validate_evidence_result(
        "get_asset_context",
        {"asset_id": "CONV-MTR-042"},
        {"error": "Asset not found"},
    )

    assert result == {
        "valid": False,
        "reason": "tool returned an error",
    }


def test_rejects_unsupported_tool():
    result = validate_evidence_result(
        "unsupported_tool",
        {"asset_id": "CONV-MTR-042"},
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "valid": False,
        "reason": "unsupported evidence tool",
    }


@pytest.mark.parametrize("invalid_id", [None, "", "   ", 123])
def test_rejects_invalid_requested_identifier(invalid_id):
    result = validate_evidence_result(
        "get_asset_context",
        {"asset_id": invalid_id},
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "valid": False,
        "reason": "invalid requested identifier",
    }


def test_rejects_missing_result_identifier():
    result = validate_evidence_result(
        "get_asset_context",
        {"asset_id": "CONV-MTR-042"},
        {"criticality": "high"},
    )

    assert result == {
        "valid": False,
        "reason": "evidence result identifier mismatch",
    }
