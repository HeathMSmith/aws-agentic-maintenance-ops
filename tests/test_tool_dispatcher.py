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
