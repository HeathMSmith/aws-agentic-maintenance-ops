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
