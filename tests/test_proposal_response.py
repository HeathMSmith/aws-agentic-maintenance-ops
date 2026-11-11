import pytest

from agent.bedrock.proposal_response import extract_action_proposal


def make_proposal_response(
    proposal=None,
    tool_name="submit_maintenance_action_proposal",
    stop_reason="tool_use",
):
    if proposal is None:
        proposal = {
            "alert_id": "ALERT-0001",
            "proposed_action": "request_expert_review",
            "reason": "Elevated vibration and temperature require expert review.",
        }

    return {
        "stopReason": stop_reason,
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "proposal-001",
                            "name": tool_name,
                            "input": proposal,
                        }
                    }
                ],
            }
        },
    }


def test_valid_proposal_response():
    result = extract_action_proposal(make_proposal_response())

    assert result["status"] == "proposed"
    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert result["proposal"]["proposed_action"] == "request_expert_review"


@pytest.mark.parametrize(
    "response",
    [
        None,
        {},
        [],
        "invalid-response",
    ],
)
def test_invalid_response_rejected(response):
    result = extract_action_proposal(response)

    assert result["status"] == "rejected"


@pytest.mark.parametrize(
    "stop_reason",
    [
        "end_turn",
        "max_tokens",
        "content_filtered",
    ],
)
def test_non_tool_use_response_rejected(stop_reason):
    result = extract_action_proposal(
        make_proposal_response(stop_reason=stop_reason)
    )

    assert result == {
        "status": "rejected",
        "reason": "model did not submit an action proposal",
    }


def test_unexpected_tool_rejected():
    result = extract_action_proposal(
        make_proposal_response(tool_name="request_equipment_shutdown")
    )

    assert result == {
        "status": "rejected",
        "reason": "unexpected proposal tool",
    }


def test_multiple_tool_requests_rejected():
    response = make_proposal_response()
    response["output"]["message"]["content"].append(
        response["output"]["message"]["content"][0].copy()
    )

    result = extract_action_proposal(response)

    assert result == {
        "status": "rejected",
        "reason": "expected exactly one action proposal",
    }


def test_missing_tool_request_rejected():
    response = make_proposal_response()
    response["output"]["message"]["content"] = []

    result = extract_action_proposal(response)

    assert result == {
        "status": "rejected",
        "reason": "expected exactly one action proposal",
    }


def test_invalid_proposal_rejected():
    response = make_proposal_response(
        proposal={
            "alert_id": "ALERT-0001",
            "proposed_action": "restart_equipment",
            "reason": "Restart immediately.",
        }
    )

    result = extract_action_proposal(response)

    assert result == {
        "status": "rejected",
        "reason": "unsupported proposed maintenance action",
    }


def test_approval_injection_rejected():
    response = make_proposal_response(
        proposal={
            "alert_id": "ALERT-0001",
            "proposed_action": "request_equipment_shutdown",
            "reason": "Shutdown required.",
            "approved": True,
        }
    )

    result = extract_action_proposal(response)

    assert result["status"] == "rejected"
    assert "proposal must contain exactly" in result["reason"]


def test_invalid_content_type_rejected():
    response = make_proposal_response()
    response["output"]["message"]["content"] = "invalid"

    result = extract_action_proposal(response)

    assert result == {
        "status": "rejected",
        "reason": "invalid proposal response content",
    }

@pytest.mark.parametrize(
    "response",
    [
        {"stopReason": "tool_use"},
        {"stopReason": "tool_use", "output": None},
        {"stopReason": "tool_use", "output": "invalid"},
        {"stopReason": "tool_use", "output": {}},
        {"stopReason": "tool_use", "output": {"message": None}},
        {"stopReason": "tool_use", "output": {"message": []}},
        {
            "stopReason": "tool_use",
            "output": {"message": {"content": None}},
        },
    ],
)
def test_malformed_nested_response_rejected(response):
    result = extract_action_proposal(response)

    assert result["status"] == "rejected"
    assert result["reason"] in {
        "invalid proposal response structure",
        "invalid proposal response content",
    }
