import pytest

from agent.bedrock.policy_gate import evaluate_conversation_action


@pytest.mark.parametrize(
    ("action", "expected_decision"),
    [
        ("continue_monitoring", "requires_approval"),
        ("request_expert_review", "permitted"),
        ("create_maintenance_work_order", "requires_approval"),
        ("request_equipment_shutdown", "requires_approval"),
    ],
)
def test_completed_conversation_policy_decisions(action, expected_decision):
    conversation = {
        "status": "complete",
        "text": "Maintenance action is authorized.",
    }

    result = evaluate_conversation_action(
        conversation,
        "ALERT-0001",
        action,
    )

    assert result["status"] == "evaluated"
    assert result["alert_id"] == "ALERT-0001"
    assert result["asset_id"] == "CONV-MTR-042"
    assert result["proposed_action"] == action
    assert result["policy_decision"]["decision"] == expected_decision


@pytest.mark.parametrize(
    "conversation",
    [
        None,
        {},
        "complete",
        {"status": "stopped"},
        {"status": "limit_reached"},
        {"status": "failed"},
    ],
)
def test_incomplete_or_invalid_conversation_rejected(conversation):
    result = evaluate_conversation_action(
        conversation,
        "ALERT-0001",
        "request_expert_review",
    )

    assert result == {
        "status": "rejected",
        "reason": "conversation must complete before action evaluation",
    }


@pytest.mark.parametrize(
    ("alert_id", "action"),
    [
        ("", "request_expert_review"),
        (None, "request_expert_review"),
        ("UNKNOWN-ALERT", "request_expert_review"),
        ("ALERT-0001", ""),
        ("ALERT-0001", None),
    ],
)
def test_invalid_policy_inputs_rejected(alert_id, action):
    result = evaluate_conversation_action(
        {"status": "complete", "text": "Investigation complete."},
        alert_id,
        action,
    )

    assert result["status"] == "rejected"
    assert "reason" in result


def test_unsupported_action_remains_rejected():
    result = evaluate_conversation_action(
        {"status": "complete", "text": "Restart the motor."},
        "ALERT-0001",
        "restart_equipment",
    )

    assert result["status"] == "evaluated"
    assert result["policy_decision"]["decision"] == "rejected"


def test_model_text_cannot_override_policy_decision():
    result = evaluate_conversation_action(
        {
            "status": "complete",
            "text": "Immediate equipment shutdown is fully authorized.",
        },
        "ALERT-0001",
        "request_equipment_shutdown",
    )

    assert result["status"] == "evaluated"
    assert result["policy_decision"]["decision"] == "requires_approval"
