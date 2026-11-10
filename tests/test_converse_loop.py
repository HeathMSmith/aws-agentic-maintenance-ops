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


def test_complete_four_tool_investigation():
    first_response = tool_request()

    second_response = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "tool-002",
                            "name": "get_asset_context",
                            "input": {"asset_id": "CONV-MTR-042"},
                        }
                    },
                    {
                        "toolUse": {
                            "toolUseId": "tool-003",
                            "name": "get_maintenance_history",
                            "input": {"asset_id": "CONV-MTR-042"},
                        }
                    },
                    {
                        "toolUse": {
                            "toolUseId": "tool-004",
                            "name": "get_production_schedule",
                            "input": {"asset_id": "CONV-MTR-042"},
                        }
                    },
                ],
            }
        },
    }

    client = FakeBedrockClient(
        [
            first_response,
            second_response,
            final_response(),
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001 using all available evidence.",
        max_model_calls=3,
    )

    assert result["status"] == "complete"
    assert result["model_calls"] == 3
    assert result["text"] == "ALERT-0001 requires investigation."

    assert result["execution_trace"] == [
        {
            "model_call": 1,
            "tool_name": "get_equipment_alert",
            "status": "success",
        },
        {
            "model_call": 2,
            "tool_name": "get_asset_context",
            "status": "success",
        },
        {
            "model_call": 2,
            "tool_name": "get_maintenance_history",
            "status": "success",
        },
        {
            "model_call": 2,
            "tool_name": "get_production_schedule",
            "status": "success",
        },
    ]

    assert len(client.calls) == 3

    # The third model request must contain all three tool results.
    messages = client.calls[2]["messages"]
    tool_results = messages[-1]["content"]

    assert len(tool_results) == 3

    assert [item["toolResult"]["toolUseId"] for item in tool_results] == [
        "tool-002",
        "tool-003",
        "tool-004",
    ]

    assert all(item["toolResult"]["status"] == "success" for item in tool_results)

    results_by_id = {
        item["toolResult"]["toolUseId"]: item["toolResult"]["content"][0]["json"]
        for item in tool_results
    }

    assert results_by_id["tool-002"]["asset_id"] == "CONV-MTR-042"
    assert results_by_id["tool-003"]["record_count"] == 2
    assert results_by_id["tool-004"]["line_id"] == "PKG-LINE-02"


def test_execution_context_propagates_across_tool_calls(monkeypatch):
    from agent.bedrock import tool_results

    captured = []

    def fake_dispatch(tool_name, tool_input, execution_context=None):
        captured.append(
            {
                "tool_name": tool_name,
                "execution_context": execution_context,
            }
        )
        return {"status": "ok"}

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch,
    )

    second_response = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "tool-002",
                            "name": "get_asset_context",
                            "input": {"asset_id": "CONV-MTR-042"},
                        }
                    }
                ],
            }
        },
    }

    client = FakeBedrockClient(
        [
            tool_request(),
            second_response,
            final_response(),
        ]
    )

    context = {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
        max_model_calls=3,
        execution_context=context,
    )

    assert result["status"] == "complete"
    assert result["model_calls"] == 3

    assert captured == [
        {
            "tool_name": "get_equipment_alert",
            "execution_context": context,
        },
        {
            "tool_name": "get_asset_context",
            "execution_context": context,
        },
    ]
