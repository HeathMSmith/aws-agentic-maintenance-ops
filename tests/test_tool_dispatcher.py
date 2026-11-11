import pytest

from agent.bedrock.tool_dispatcher import dispatch_tool


def test_valid_alert_lookup():
    result = dispatch_tool(
        "get_equipment_alert",
        {"alert_id": "ALERT-0001"},
    )

    assert result["alert_id"] == "ALERT-0001"
    assert result["asset_id"] == "CONV-MTR-042"
    assert result["severity"] == "warning"


def test_nonexistent_alert():
    result = dispatch_tool(
        "get_equipment_alert",
        {"alert_id": "ALERT-DOES-NOT-EXIST"},
    )

    assert isinstance(result, dict)
    assert result.get("alert_id") != "ALERT-0001"


def test_unsupported_tool():
    result = dispatch_tool(
        "delete_equipment_alert",
        {"alert_id": "ALERT-0001"},
    )

    assert result == {
        "error": "unsupported_tool",
        "message": "Tool 'delete_equipment_alert' is not allowed",
    }


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"alert_id": ""},
        {"alert_id": "   "},
        {"alert_id": None},
        {"alert_id": 123},
        {"alert_id": "ALERT-0001", "extra": "unexpected"},
        None,
        "ALERT-0001",
    ],
)
def test_invalid_tool_arguments(tool_input):
    result = dispatch_tool(
        "get_equipment_alert",
        tool_input,
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": "get_equipment_alert requires a non-empty alert_id string",
    }


def test_valid_asset_context_lookup():
    result = dispatch_tool(
        "get_asset_context",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["criticality"] == "high"


def test_nonexistent_asset_context():
    result = dispatch_tool(
        "get_asset_context",
        {"asset_id": "ASSET-DOES-NOT-EXIST"},
    )

    assert result == {
        "error": "Asset not found: ASSET-DOES-NOT-EXIST",
    }


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"asset_id": ""},
        {"asset_id": "   "},
        {"asset_id": None},
        {"asset_id": 123},
        {"asset_id": "CONV-MTR-042", "extra": "unexpected"},
        None,
        "CONV-MTR-042",
    ],
)
def test_invalid_asset_context_arguments(tool_input):
    result = dispatch_tool(
        "get_asset_context",
        tool_input,
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": "get_asset_context requires a non-empty asset_id string",
    }


def test_unsupported_asset_operation():
    result = dispatch_tool(
        "delete_asset",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "error": "unsupported_tool",
        "message": "Tool 'delete_asset' is not allowed",
    }


def test_valid_maintenance_history_lookup():
    result = dispatch_tool(
        "get_maintenance_history",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["record_count"] == 2
    assert [record["record_id"] for record in result["records"]] == [
        "MAINT-0002",
        "MAINT-0001",
    ]


def test_empty_maintenance_history():
    result = dispatch_tool(
        "get_maintenance_history",
        {"asset_id": "UNKNOWN-ASSET"},
    )

    assert result == {
        "asset_id": "UNKNOWN-ASSET",
        "record_count": 0,
        "records": [],
    }


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"asset_id": ""},
        {"asset_id": "   "},
        {"asset_id": None},
        {"asset_id": 123},
        {"asset_id": "CONV-MTR-042", "extra": "unexpected"},
        None,
        "CONV-MTR-042",
    ],
)
def test_invalid_maintenance_history_arguments(tool_input):
    result = dispatch_tool(
        "get_maintenance_history",
        tool_input,
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": (
            "get_maintenance_history requires a non-empty asset_id string"
        ),
    }


def test_unsupported_maintenance_operation():
    result = dispatch_tool(
        "delete_maintenance_record",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "error": "unsupported_tool",
        "message": "Tool 'delete_maintenance_record' is not allowed",
    }


def test_valid_production_schedule_lookup():
    result = dispatch_tool(
        "get_production_schedule",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["line_id"] == "PKG-LINE-02"
    assert len(result["schedule"]) == 2

    assert [entry["activity"] for entry in result["schedule"]] == [
        "scheduled_production",
        "planned_maintenance_window",
    ]


def test_missing_production_schedule():
    result = dispatch_tool(
        "get_production_schedule",
        {"asset_id": "UNKNOWN-ASSET"},
    )

    assert result == {
        "error": "No production schedule found for asset: UNKNOWN-ASSET",
    }


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"asset_id": ""},
        {"asset_id": "   "},
        {"asset_id": None},
        {"asset_id": 123},
        {"asset_id": "CONV-MTR-042", "extra": "unexpected"},
        None,
        "CONV-MTR-042",
    ],
)
def test_invalid_production_schedule_arguments(tool_input):
    result = dispatch_tool(
        "get_production_schedule",
        tool_input,
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": (
            "get_production_schedule requires a non-empty asset_id string"
        ),
    }


def test_unsupported_production_schedule_operation():
    result = dispatch_tool(
        "delete_production_schedule",
        {"asset_id": "CONV-MTR-042"},
    )

    assert result == {
        "error": "unsupported_tool",
        "message": "Tool 'delete_production_schedule' is not allowed",
    }


def test_existing_tool_accepts_execution_context():
    result = dispatch_tool(
        "get_asset_context",
        {"asset_id": "CONV-MTR-042"},
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["criticality"] == "high"

def test_maintenance_window_status_with_valid_context():
    result = dispatch_tool(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["line_id"] == "PKG-LINE-02"
    assert result["reference_timestamp"] == "2026-11-10T18:00:00Z"

    assert result["maintenance_window"] == {
        "available": False,
        "reason": "No upcoming maintenance window found",
    }


def test_maintenance_window_status_at_incident_time():
    result = dispatch_tool(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        execution_context={
            "reference_timestamp": "2026-11-09T14:30:00Z",
        },
    )

    window = result["maintenance_window"]

    assert window["available"] is True
    assert window["schedule_id"] == "MAINT-WINDOW-0001"
    assert window["hours_until_start"] == 7.5
    assert window["remaining_duration_hours"] == 4.0


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"asset_id": ""},
        {"asset_id": "   "},
        {"asset_id": None},
        {"asset_id": 123},
        {"asset_id": "CONV-MTR-042", "extra": "unexpected"},
        {"asset_id": "CONV-MTR-042", "reference_timestamp": "2026-11-09T14:30:00Z"},
        None,
        "CONV-MTR-042",
    ],
)
def test_maintenance_window_status_invalid_arguments(tool_input):
    result = dispatch_tool(
        "get_maintenance_window_status",
        tool_input,
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": (
            "get_maintenance_window_status requires "
            "a non-empty asset_id string"
        ),
    }


@pytest.mark.parametrize(
    "execution_context",
    [
        None,
        {},
        {"other_field": "value"},
        "2026-11-10T18:00:00Z",
    ],
)
def test_maintenance_window_status_missing_context(execution_context):
    result = dispatch_tool(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        execution_context=execution_context,
    )

    assert result == {
        "error": "missing_execution_context",
        "message": "A trusted reference_timestamp is required",
    }


@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "invalid-timestamp",
        "2026-11-10T18:00:00",
        None,
        123,
    ],
)
def test_maintenance_window_status_invalid_context_timestamp(timestamp):
    result = dispatch_tool(
        "get_maintenance_window_status",
        {"asset_id": "CONV-MTR-042"},
        execution_context={
            "reference_timestamp": timestamp,
        },
    )

    assert result == {
        "error": "invalid_execution_context",
        "message": (
            "reference_timestamp must be a timezone-aware "
            "ISO 8601 timestamp"
        ),
    }


def test_maintenance_window_status_missing_schedule():
    result = dispatch_tool(
        "get_maintenance_window_status",
        {"asset_id": "UNKNOWN-ASSET"},
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result == {
        "error": "No production schedule found for asset: UNKNOWN-ASSET",
    }
@pytest.mark.parametrize(
    ("action", "expected_decision"),
    [
        ("continue_monitoring", "requires_approval"),
        ("request_expert_review", "permitted"),
        ("create_maintenance_work_order", "requires_approval"),
        ("request_equipment_shutdown", "requires_approval"),
    ],
)
def test_dispatch_maintenance_action_evaluation(action, expected_decision):
    result = dispatch_tool(
        "evaluate_proposed_maintenance_action",
        {
            "alert_id": "ALERT-0001",
            "action": action,
        },
    )

    assert result["alert_id"] == "ALERT-0001"
    assert result["asset_id"] == "CONV-MTR-042"
    assert result["action"] == action
    assert result["policy_decision"]["decision"] == expected_decision


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"alert_id": "ALERT-0001"},
        {"action": "request_expert_review"},
        {"alert_id": "", "action": "request_expert_review"},
        {"alert_id": "ALERT-0001", "action": ""},
        {"alert_id": None, "action": "request_expert_review"},
        {"alert_id": "ALERT-0001", "action": None},
        {"alert_id": 123, "action": "request_expert_review"},
        {"alert_id": "ALERT-0001", "action": 123},
        {
            "alert_id": "ALERT-0001",
            "action": "request_equipment_shutdown",
            "approved": True,
        },
        None,
        "ALERT-0001",
    ],
)
def test_dispatch_maintenance_action_invalid_input(tool_input):
    result = dispatch_tool(
        "evaluate_proposed_maintenance_action",
        tool_input,
    )

    assert result == {
        "error": "invalid_tool_input",
        "message": (
            "evaluate_proposed_maintenance_action requires "
            "non-empty alert_id and action strings"
        ),
    }


def test_dispatch_maintenance_action_unsupported_action():
    result = dispatch_tool(
        "evaluate_proposed_maintenance_action",
        {
            "alert_id": "ALERT-0001",
            "action": "restart_equipment",
        },
    )

    assert result["policy_decision"]["decision"] == "rejected"
    assert "Unsupported maintenance action" in (
        result["policy_decision"]["reason"]
    )


def test_dispatch_maintenance_action_unknown_alert():
    result = dispatch_tool(
        "evaluate_proposed_maintenance_action",
        {
            "alert_id": "UNKNOWN-ALERT",
            "action": "request_expert_review",
        },
    )

    assert result["error"] == "investigation_failed"
