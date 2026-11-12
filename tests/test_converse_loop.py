from copy import deepcopy

import pytest

from agent.bedrock import execution_context
from agent.bedrock.converse_loop import run_conversation
from datetime import datetime, timezone
from unittest.mock import patch
from agent.tools.equipment_alert import get_equipment_alert


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

    evidence_records = result["evidence_records"]

    assert len(evidence_records) == 1

    record = evidence_records[0]

    assert record["tool_name"] == "get_equipment_alert"
    assert record["tool_use_id"] == "tool-001"
    assert record["identifiers"] == {"alert_id": "ALERT-0001"}
    assert record["result"] == get_equipment_alert("ALERT-0001")
    assert len(record["sha256"]) == 64

    assert result == {
        "status": "complete",
        "text": "ALERT-0001 requires investigation.",
        "model_calls": 2,
        "execution_trace": [
            {
                "model_call": 1,
                "tool_name": "get_equipment_alert",
                "status": "success",
                "identifiers": {
                    "alert_id": "ALERT-0001",
                },
            }
        ],
        "evidence_records": evidence_records,
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
                "identifiers": {
                    "alert_id": "ALERT-0001",
                },
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
            "identifiers": {
                "alert_id": "ALERT-0001",
            },
        },
        {
            "model_call": 2,
            "tool_name": "get_asset_context",
            "status": "success",
            "identifiers": {
                "asset_id": "CONV-MTR-042",
            },
        },
        {
            "model_call": 2,
            "tool_name": "get_maintenance_history",
            "status": "success",
            "identifiers": {
                "asset_id": "CONV-MTR-042",
            },
        },
        {
            "model_call": 2,
            "tool_name": "get_production_schedule",
            "status": "success",
            "identifiers": {
                "asset_id": "CONV-MTR-042",
            },
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


def test_run_conversation_creates_execution_context():
    fixed_time = datetime(2026, 11, 11, 14, 30, tzinfo=timezone.utc)

    response = {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Investigation complete."}],
            }
        },
    }

    class FakeClient:
        def converse(self, **kwargs):
            return response

    with (
        patch("agent.bedrock.execution_context.datetime") as mock_datetime,
        patch("agent.bedrock.converse_loop.handle_converse_response") as mock_handler,
    ):
        mock_datetime.now.return_value = fixed_time

        mock_handler.return_value = {
            "status": "complete",
            "text": "Investigation complete.",
        }

        run_conversation(
            client=FakeClient(),
            model_id="test-model",
            prompt="Investigate the equipment alert.",
        )

        mock_handler.assert_called_once()

        execution_context = mock_handler.call_args.kwargs["execution_context"]

        assert execution_context == {"reference_timestamp": "2026-11-11T14:30:00Z"}

        mock_datetime.now.assert_called_once_with(timezone.utc)


def test_run_conversation_normalizes_historical_execution_context():
    response = {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Investigation complete."}],
            }
        },
    }

    class FakeClient:
        def converse(self, **kwargs):
            return response

    with patch("agent.bedrock.converse_loop.handle_converse_response") as mock_handler:
        mock_handler.return_value = {
            "status": "complete",
            "text": "Investigation complete.",
        }

        run_conversation(
            client=FakeClient(),
            model_id="test-model",
            prompt="Investigate the historical equipment alert.",
            execution_context={
                "reference_timestamp": "2026-11-10T13:00:00-05:00",
            },
        )

        mock_handler.assert_called_once()

        execution_context = mock_handler.call_args.kwargs["execution_context"]

        assert execution_context == {"reference_timestamp": "2026-11-10T18:00:00Z"}


def test_conversation_executes_maintenance_window_tool_with_trusted_timestamp():
    tool_request = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "window-tool-001",
                            "name": "get_maintenance_window_status",
                            "input": {"asset_id": "CONV-MTR-042"},
                        }
                    }
                ],
            }
        },
    }

    final_response = {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Maintenance window unavailable."}],
            }
        },
    }

    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return tool_request

            return final_response

    client = FakeClient()

    result = run_conversation(
        client=client,
        model_id="test-model",
        prompt="Check the maintenance window for CONV-MTR-042.",
        execution_context={
            "reference_timestamp": "2026-11-10T13:00:00-05:00",
        },
    )

    assert result["status"] == "complete"
    assert len(client.calls) == 2

    messages = client.calls[1]["messages"]

    tool_results = [
        block["toolResult"]
        for message in messages
        for block in message["content"]
        if "toolResult" in block
    ]

    assert len(tool_results) == 1

    tool_result = tool_results[0]

    assert tool_result["toolUseId"] == "window-tool-001"

    payload = tool_result["content"][0]["json"]

    assert payload["asset_id"] == "CONV-MTR-042"
    assert payload["reference_timestamp"] == "2026-11-10T18:00:00Z"
    assert payload["maintenance_window"] == {
        "available": False,
        "reason": "No upcoming maintenance window found",
    }

def test_execution_trace_excludes_unrelated_tool_arguments():
    response = tool_request()

    tool_input = response["output"]["message"]["content"][0]["toolUse"]["input"]

    tool_input["debug_notes"] = "Do not include in execution trace"
    tool_input["internal_metadata"] = {
        "source": "simulated",
        "details": "Should not be recorded",
    }

    client = FakeBedrockClient(
        [
            response,
            final_response(),
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
    )

    assert result["status"] == "complete"

    assert result["execution_trace"] == [
        {
            "model_call": 1,
            "tool_name": "get_equipment_alert",
            "status": "error",
            "identifiers": {
                "alert_id": "ALERT-0001",
            },
        }
    ]

def test_execution_trace_excludes_malformed_identifier():
    response = tool_request()

    tool_input = response["output"]["message"]["content"][0]["toolUse"]["input"]

    tool_input["alert_id"] = 123

    client = FakeBedrockClient(
        [
            response,
            final_response(),
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Investigate ALERT-0001",
    )

    assert result["status"] == "complete"

    assert result["execution_trace"] == [
        {
            "model_call": 1,
            "tool_name": "get_equipment_alert",
            "status": "error",
            "identifiers": {},
        }
    ]

def test_failed_tool_result_is_not_recorded_as_evidence(monkeypatch):
    """Failed evidence retrieval must not create a trusted record."""

    from agent.bedrock import tool_results

    def fake_dispatch(tool_name, tool_input, execution_context=None):
        return {
            "error": "simulated_failure",
            "message": "Equipment alert retrieval failed",
        }

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch,
    )

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

    assert result["status"] == "complete"

    assert len(result["execution_trace"]) == 1
    assert result["execution_trace"][0]["status"] == "error"

    assert result["evidence_records"] == []

def test_successful_policy_tool_is_not_recorded_as_evidence(monkeypatch):
    """Successful policy evaluations must not become evidence records."""

    from agent.bedrock import tool_results

    def fake_dispatch(tool_name, tool_input, execution_context=None):
        assert tool_name == "evaluate_proposed_maintenance_action"

        return {
            "action": "request_equipment_shutdown",
            "decision": "requires_approval",
        }

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch,
    )

    policy_tool_request = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "policy-001",
                            "name": "evaluate_proposed_maintenance_action",
                            "input": {
                                "proposed_action": "request_equipment_shutdown",
                            },
                        }
                    }
                ],
            }
        },
    }

    client = FakeBedrockClient(
        [
            policy_tool_request,
            final_response(),
        ]
    )

    result = run_conversation(
        client,
        "simulated-model",
        "Evaluate the proposed maintenance action",
    )

    assert result["status"] == "complete"

    trace = result["execution_trace"]

    assert len(trace) == 1
    assert trace[0]["tool_name"] == "evaluate_proposed_maintenance_action"
    assert trace[0]["status"] == "success"

    assert result["evidence_records"] == []
