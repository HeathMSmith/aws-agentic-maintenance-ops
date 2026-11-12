import pytest

from agent.bedrock.proposal_generator import generate_action_proposal
from agent.bedrock.proposal_tool_spec import PROPOSAL_TOOL_CONFIG


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def make_proposal_response(
    alert_id="ALERT-0001",
    action="request_expert_review",
):
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "proposal-001",
                            "name": "submit_maintenance_action_proposal",
                            "input": {
                                "alert_id": alert_id,
                                "proposed_action": action,
                                "reason": (
                                    "Elevated vibration and temperature "
                                    "require expert inspection."
                                ),
                            },
                        }
                    }
                ],
            }
        },
    }

def test_generate_valid_action_proposal():
    client = FakeClient(make_proposal_response())

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Elevated vibration and temperature detected.",
        },
        alert_id="ALERT-0001",
    )

    assert result["status"] == "proposed"
    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert result["proposal"]["proposed_action"] == "request_expert_review"

    assert len(client.calls) == 1

    request = client.calls[0]

    assert request["modelId"] == "test-model"
    assert request["toolConfig"] == PROPOSAL_TOOL_CONFIG
    assert request["inferenceConfig"] == {"maxTokens": 1024}


def test_proposal_prompt_includes_validated_operational_facts():
    client = FakeClient(make_proposal_response())

    operational_facts = {
        "asset_id": "CONV-MTR-042",
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "maintenance_window_available": False,
    }

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Elevated vibration and temperature detected.",
        },
        alert_id="ALERT-0001",
        operational_facts=operational_facts,
    )

    assert result["status"] == "proposed"
    assert len(client.calls) == 1

    prompt = client.calls[0]["messages"][0]["content"][0]["text"]

    assert "2026-11-10T18:00:00Z" in prompt
    assert "CONV-MTR-042" in prompt
    assert "maintenance_window_available" in prompt
    assert "false" in prompt.lower()


@pytest.mark.parametrize(
    "investigation_result",
    [
        None,
        {},
        {"status": "stopped"},
        {"status": "limit_reached"},
        {"status": "failed"},
    ],
)

def test_incomplete_investigation_rejected(investigation_result):
    client = FakeClient(make_proposal_response())

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result=investigation_result,
        alert_id="ALERT-0001",
    )

    assert result == {
        "status": "rejected",
        "reason": "investigation must complete before proposal generation",
    }

    assert client.calls == []


@pytest.mark.parametrize(
    "alert_id",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_invalid_alert_id_rejected(alert_id):
    client = FakeClient(make_proposal_response())

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Investigation complete.",
        },
        alert_id=alert_id,
    )

    assert result == {
        "status": "rejected",
        "reason": "alert_id must be a non-empty string",
    }

    assert client.calls == []


def test_invalid_model_proposal_rejected():
    client = FakeClient(
        make_proposal_response(action="restart_equipment")
    )

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Investigation complete.",
        },
        alert_id="ALERT-0001",
    )

    assert result == {
        "status": "rejected",
        "reason": "unsupported proposed maintenance action",
    }


def test_missing_proposal_rejected():
    client = FakeClient({
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "No proposal submitted."}],
            }
        },
    })

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Investigation complete.",
        },
        alert_id="ALERT-0001",
    )

    assert result == {
        "status": "rejected",
        "reason": "model did not submit an action proposal",
    }


def test_malformed_bedrock_response_rejected():
    client = FakeClient({
        "stopReason": "tool_use",
        "output": None,
    })

    result = generate_action_proposal(
        client=client,
        model_id="test-model",
        investigation_result={
            "status": "complete",
            "text": "Investigation complete.",
        },
        alert_id="ALERT-0001",
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid proposal response structure",
    }
