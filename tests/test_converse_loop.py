from copy import deepcopy

import pytest

from agent.bedrock.converse_loop import run_conversation


def tool_request():
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "tool-001",
                            "name": "get_equipment_alert",
                            "input": {"alert_id": "ALERT-0001"},
                        }
                    }
                ],
            }
        },
    }


def final_response():
    return {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "ALERT-0001 requires investigation."}],
            }
        },
    }


class FakeBedrockClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        return deepcopy(self.responses[len(self.calls) - 1])


def test_complete_tool_use_cycle():
    client = FakeBedrockClient(
        [
            tool_request(),
            final_response(),
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
    )

    assert result == {
        "status": "complete",
        "text": "ALERT-0001 requires investigation.",
        "model_calls": 2,
        "execution_trace": [
            {
                "model_call": 1,
                "tool_name": "get_equipment_alert",
                "status": "success",
            }
        ],
    }

    assert len(client.calls) == 2

    messages = client.calls[1]["messages"]

    assert [message["role"] for message in messages] == [
        "user",
        "assistant",
        "user",
    ]

    tool_result = messages[2]["content"][0]["toolResult"]

    assert tool_result["toolUseId"] == "tool-001"
    assert tool_result["status"] == "success"
    assert tool_result["content"][0]["json"]["alert_id"] == "ALERT-0001"


def test_model_call_limit():
    client = FakeBedrockClient([tool_request()])

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
        max_model_calls=1,
    )

    assert result == {
        "status": "limit_reached",
        "reason": "maximum model calls reached",
        "execution_trace": [
            {
                "model_call": 1,
                "tool_name": "get_equipment_alert",
                "status": "success",
            }
        ],
    }

    assert len(client.calls) == 1


@pytest.mark.parametrize("max_model_calls", [0, -1, True, 1.5])
def test_reject_invalid_model_call_limit(max_model_calls):
    client = FakeBedrockClient([])

    with pytest.raises(ValueError, match="max_model_calls"):
        run_conversation(
            client,
            "simulated-model",
            "Investigate ALERT-0001",
            max_model_calls=max_model_calls,
        )

    assert client.calls == []


@pytest.mark.parametrize("prompt", ["", "   ", None, 123])
def test_reject_invalid_prompt(prompt):
    client = FakeBedrockClient([])

    with pytest.raises(ValueError, match="prompt"):
        run_conversation(
            client,
            "simulated-model",
            prompt,
        )

    assert client.calls == []


def test_unexpected_stop_reason():
    client = FakeBedrockClient(
        [
            {
                "stopReason": "max_tokens",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [],
                    }
                },
            }
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
    )

    assert result == {
        "status": "stopped",
        "reason": "max_tokens",
        "execution_trace": [],
    }

    assert len(client.calls) == 1
