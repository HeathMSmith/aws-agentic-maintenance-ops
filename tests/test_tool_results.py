import pytest

from agent.bedrock.tool_results import build_tool_result_message
from agent.tools.asset_context import get_asset_context


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


def test_execution_context_forwarded_to_dispatcher(monkeypatch):
    from agent.bedrock import tool_results

    captured = {}

    def fake_dispatch(tool_name, tool_input, execution_context=None):
        captured["tool_name"] = tool_name
        captured["tool_input"] = tool_input
        captured["execution_context"] = execution_context

        return get_asset_context("CONV-MTR-042")

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch,
    )

    context = {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }

    tool_use = {
        "toolUseId": "tool-001",
        "name": "get_asset_context",
        "input": {"asset_id": "CONV-MTR-042"},
    }

    message = tool_results.build_tool_result_message(
        tool_use,
        execution_context=context,
    )

    assert captured == {
        "tool_name": "get_asset_context",
        "tool_input": {"asset_id": "CONV-MTR-042"},
        "execution_context": context,
    }

    tool_result = message["content"][0]["toolResult"]

    assert tool_result["toolUseId"] == "tool-001"
    assert tool_result["status"] == "success"
    assert tool_result["content"][0]["json"] == get_asset_context(
        "CONV-MTR-042"
    )

def test_rejects_mismatched_evidence_result(monkeypatch):
    from agent.bedrock import tool_results

    def fake_dispatch_tool(
        tool_name,
        tool_input,
        execution_context=None,
    ):
        return {
            "asset_id": "CONV-MTR-999",
            "criticality": "high",
        }

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch_tool,
    )

    tool_use = {
        "toolUseId": "tool-mismatch-001",
        "name": "get_asset_context",
        "input": {
            "asset_id": "CONV-MTR-042",
        },
    }

    message = tool_results.build_tool_result_message(tool_use)

    result = message["content"][0]["toolResult"]

    assert result["toolUseId"] == "tool-mismatch-001"
    assert result["status"] == "error"

    assert result["content"] == [
        {
            "json": {
                "error": "invalid_evidence_result",
                "message": "evidence result identifier mismatch",
            }
        }
    ]

def test_accepts_matching_evidence_result(monkeypatch):
    from agent.bedrock import tool_results

    expected_evidence = get_asset_context("CONV-MTR-042")

    def fake_dispatch_tool(
        tool_name,
        tool_input,
        execution_context=None,
    ):
        return expected_evidence

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch_tool,
    )

    tool_use = {
        "toolUseId": "tool-match-001",
        "name": "get_asset_context",
        "input": {
            "asset_id": "CONV-MTR-042",
        },
    }

    message = tool_results.build_tool_result_message(tool_use)

    result = message["content"][0]["toolResult"]

    assert result["toolUseId"] == "tool-match-001"
    assert result["status"] == "success"
    assert result["content"] == [
        {
            "json": expected_evidence,
        }
    ]

def test_policy_evaluation_bypasses_evidence_result_validation(monkeypatch):
    from agent.bedrock import tool_results

    expected_policy_result = {
        "alert_id": "ALERT-0001",
        "proposed_action": "request_equipment_shutdown",
        "policy_decision": {
            "decision": "requires_approval",
        },
    }

    def fake_dispatch_tool(
        tool_name,
        tool_input,
        execution_context=None,
    ):
        assert tool_name == "evaluate_proposed_maintenance_action"
        return expected_policy_result

    monkeypatch.setattr(
        tool_results,
        "dispatch_tool",
        fake_dispatch_tool,
    )

    tool_use = {
        "toolUseId": "policy-001",
        "name": "evaluate_proposed_maintenance_action",
        "input": {
            "alert_id": "ALERT-0001",
            "action": "request_equipment_shutdown",
        },
    }

    message = tool_results.build_tool_result_message(tool_use)

    result = message["content"][0]["toolResult"]

    assert result["toolUseId"] == "policy-001"
    assert result["status"] == "success"
    assert result["content"] == [
        {
            "json": expected_policy_result,
        }
    ]
