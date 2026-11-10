import pytest

from agent.bedrock.response_handler import handle_converse_response


def make_response(stop_reason, content):
    return {
        "stopReason": stop_reason,
        "output": {
            "message": {
                "role": "assistant",
                "content": content,
            }
        },
    }


def test_successful_tool_request():
    response = make_response(
        "tool_use",
        [
            {
                "toolUse": {
                    "toolUseId": "tool-001",
                    "name": "get_equipment_alert",
                    "input": {"alert_id": "ALERT-0001"},
                }
            }
        ],
    )

    result = handle_converse_response(response)

    assert result["status"] == "tool_results"
    assert len(result["messages"]) == 1

    tool_result = result["messages"][0]["content"][0]["toolResult"]

    assert tool_result["toolUseId"] == "tool-001"
    assert tool_result["status"] == "success"
    assert tool_result["content"][0]["json"]["alert_id"] == "ALERT-0001"


def test_failed_tool_request():
    response = make_response(
        "tool_use",
        [
            {
                "toolUse": {
                    "toolUseId": "tool-002",
                    "name": "get_equipment_alert",
                    "input": {"alert_id": "ALERT-NOT-FOUND"},
                }
            }
        ],
    )

    result = handle_converse_response(response)

    assert result["status"] == "tool_results"

    tool_result = result["messages"][0]["content"][0]["toolResult"]

    assert tool_result["status"] == "error"
    assert "Alert not found" in tool_result["content"][0]["json"]["error"]


def test_multiple_tool_requests():
    response = make_response(
        "tool_use",
        [
            {
                "toolUse": {
                    "toolUseId": "tool-001",
                    "name": "get_equipment_alert",
                    "input": {"alert_id": "ALERT-0001"},
                }
            },
            {
                "toolUse": {
                    "toolUseId": "tool-002",
                    "name": "get_equipment_alert",
                    "input": {"alert_id": "ALERT-NOT-FOUND"},
                }
            },
        ],
    )

    result = handle_converse_response(response)

    assert len(result["messages"]) == 2

    statuses = [
        message["content"][0]["toolResult"]["status"]
        for message in result["messages"]
    ]

    assert statuses == ["success", "error"]


def test_final_text_response():
    response = make_response(
        "end_turn",
        [{"text": "The equipment requires further investigation."}],
    )

    result = handle_converse_response(response)

    assert result == {
        "status": "complete",
        "text": "The equipment requires further investigation.",
    }


def test_multiple_text_blocks():
    response = make_response(
        "end_turn",
        [
            {"text": "First observation."},
            {"text": "Second observation."},
        ],
    )

    result = handle_converse_response(response)

    assert result["text"] == (
        "First observation.\nSecond observation."
    )


@pytest.mark.parametrize(
    "stop_reason",
    [
        "max_tokens",
        "stop_sequence",
        "guardrail_intervened",
        "content_filtered",
    ],
)
def test_unexpected_stop_reason(stop_reason):
    response = make_response(stop_reason, [])

    result = handle_converse_response(response)

    assert result == {
        "status": "unexpected_stop",
        "reason": stop_reason,
    }
