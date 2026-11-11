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

    evidence = {identifier_field: identifier}

    if tool_name == "get_maintenance_history":
        evidence.update({
            "record_count": 0,
            "records": [],
        })

    if tool_name == "get_production_schedule":
        evidence["schedule"] = []

    if tool_name == "get_maintenance_window_status":
        evidence["maintenance_window"] = {
            "available": False,
            "reason": "No upcoming maintenance window found",
        }

    result = validate_evidence_result(
        tool_name,
        {identifier_field: identifier},
        evidence,
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

@pytest.mark.parametrize(
    "record_count,records",
    [
        (2, []),
        (0, [{"asset_id": "CONV-MTR-042"}]),
        (-1, []),
        (True, []),
        ("2", []),
        (None, []),
    ],
)
def test_rejects_inconsistent_maintenance_history(
    record_count,
    records,
):
    result = validate_evidence_result(
        "get_maintenance_history",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "record_count": record_count,
            "records": records,
        },
    )

    assert result == {
        "valid": False,
        "reason": "invalid maintenance history structure",
    }

@pytest.mark.parametrize(
    "invalid_record",
    [
        None,
        "invalid",
        123,
        {},
        {"asset_id": "CONV-MTR-999"},
        {"asset_id": None},
    ],
)
def test_rejects_invalid_maintenance_record(invalid_record):
    result = validate_evidence_result(
        "get_maintenance_history",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "record_count": 1,
            "records": [invalid_record],
        },
    )

    assert result == {
        "valid": False,
        "reason": "invalid maintenance history structure",
    }

def test_accepts_valid_production_schedule_interval():
    result = validate_evidence_result(
        "get_production_schedule",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "schedule": [
                {
                    "schedule_id": "PROD-0001",
                    "start": "2026-11-09T06:00:00Z",
                    "end": "2026-11-09T22:00:00Z",
                    "activity": "scheduled_production",
                }
            ],
        },
    )

    assert result == {"valid": True}

@pytest.mark.parametrize(
    "start,end",
    [
        # Start and end are identical
        ("2026-11-09T22:00:00Z", "2026-11-09T22:00:00Z"),

        # End precedes start
        ("2026-11-09T22:00:00Z", "2026-11-09T06:00:00Z"),

        # Invalid timestamp
        ("not-a-timestamp", "2026-11-09T22:00:00Z"),

        # Missing timezone
        ("2026-11-09T06:00:00", "2026-11-09T22:00:00Z"),

        # Missing start
        (None, "2026-11-09T22:00:00Z"),

        # Missing end
        ("2026-11-09T06:00:00Z", None),

        # Incorrect timestamp type
        (123, "2026-11-09T22:00:00Z"),
    ],
)
def test_rejects_invalid_production_schedule_interval(start, end):
    result = validate_evidence_result(
        "get_production_schedule",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "schedule": [
                {
                    "schedule_id": "PROD-0001",
                    "start": start,
                    "end": end,
                    "activity": "scheduled_production",
                }
            ],
        },
    )

    assert result == {
        "valid": False,
        "reason": "invalid production schedule structure",
    }

@pytest.mark.parametrize(
    "schedule",
    [
        None,
        {},
        "invalid",
        123,
        [None],
        ["invalid"],
        [123],
        [{}],
    ],
)
def test_rejects_malformed_production_schedule(schedule):
    result = validate_evidence_result(
        "get_production_schedule",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "schedule": schedule,
        },
    )

    assert result == {
        "valid": False,
        "reason": "invalid production schedule structure",
    }

@pytest.mark.parametrize(
    "available,expected_valid",
    [
        (True, True),
        (False, True),
        ("true", False),
        ("false", False),
        (1, False),
        (0, False),
        (None, False),
    ],
)
def test_maintenance_window_availability_type(
    available,
    expected_valid,
):
    result = validate_evidence_result(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "maintenance_window": {
                "available": available,
            },
        },
    )

    assert result["valid"] is expected_valid

    if not expected_valid:
        assert result["reason"] == (
            "invalid maintenance window structure"
        )

@pytest.mark.parametrize(
    "maintenance_window",
    [
        None,
        {},
        [],
        "invalid",
        123,
        {"available": None},
        {"available": "false"},
    ],
)
def test_rejects_malformed_maintenance_window(maintenance_window):
    result = validate_evidence_result(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        {
            "asset_id": "CONV-MTR-042",
            "maintenance_window": maintenance_window,
        },
    )

    assert result == {
        "valid": False,
        "reason": "invalid maintenance window structure",
    }
