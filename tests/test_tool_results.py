import pytest

from agent.bedrock.tool_results import build_tool_result_message


def make_tool_use(tool_name, tool_input):
    return {
        "toolUseId": "test-tool-use-001",
        "name": tool_name,
        "input": tool_input,
    }


def test_successful_tool_result():
    tool_use = make_tool_use(
        "get_equipment_alert",
        {"alert_id": "ALERT-0001"},
    )

    message = build_tool_result_message(tool_use)

    assert message["role"] == "user"

    result = message["content"][0]["toolResult"]

    assert result["toolUseId"] == "test-tool-use-001"
    assert result["status"] == "success"
    assert result["content"][0]["json"]["alert_id"] == "ALERT-0001"


def test_missing_alert_returns_error():
    tool_use = make_tool_use(
        "get_equipment_alert",
        {"alert_id": "ALERT-DOES-NOT-EXIST"},
    )

    message = build_tool_result_message(tool_use)
    result = message["content"][0]["toolResult"]

    assert result["status"] == "error"
    assert "Alert not found" in result["content"][0]["json"]["error"]


def test_unsupported_tool_returns_error():
    tool_use = make_tool_use(
        "delete_equipment_alert",
        {"alert_id": "ALERT-0001"},
    )

    message = build_tool_result_message(tool_use)
    result = message["content"][0]["toolResult"]

    assert result["status"] == "error"
    assert result["content"][0]["json"]["error"] == "unsupported_tool"


@pytest.mark.parametrize(
    "tool_input",
    [
        {},
        {"alert_id": ""},
        {"alert_id": None},
        {"alert_id": 123},
        {"alert_id": "ALERT-0001", "extra": "unexpected"},
    ],
)
def test_invalid_tool_input_returns_error(tool_input):
    tool_use = make_tool_use("get_equipment_alert", tool_input)

    message = build_tool_result_message(tool_use)
    result = message["content"][0]["toolResult"]

    assert result["status"] == "error"
    assert result["content"][0]["json"]["error"] == "invalid_tool_input"
