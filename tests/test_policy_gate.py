import pytest

from agent.bedrock.policy_gate import (
    evaluate_conversation_action,
    evaluate_structured_action_proposal,
)


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

@pytest.mark.parametrize(
    ("action", "expected_decision"),
    [
        ("continue_monitoring", "requires_approval"),
        ("request_expert_review", "permitted"),
        ("create_maintenance_work_order", "requires_approval"),
        ("request_equipment_shutdown", "requires_approval"),
    ],
)
def test_structured_proposal_policy_decisions(action, expected_decision):
    conversation = {
        "status": "complete",
        "text": "Investigation complete.",
    }

    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": action,
        "reason": "Equipment anomaly requires assessment.",
    }

    result = evaluate_structured_action_proposal(
        conversation,
        "ALERT-0001",
        proposal,
    )

    assert result["status"] == "evaluated"
    assert result["alert_id"] == "ALERT-0001"
    assert result["proposed_action"] == action
    assert result["policy_decision"]["decision"] == expected_decision


def test_structured_proposal_rejects_mismatched_alert():
    proposal = {
        "alert_id": "ALERT-9999",
        "proposed_action": "request_expert_review",
        "reason": "Expert inspection required.",
    }

    result = evaluate_structured_action_proposal(
        {"status": "complete"},
        "ALERT-0001",
        proposal,
    )

    assert result == {
        "status": "rejected",
        "reason": "proposal alert_id does not match the requested incident",
    }


def test_structured_proposal_rejects_approval_injection():
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "request_equipment_shutdown",
        "reason": "Elevated vibration and temperature.",
        "approved": True,
    }

    result = evaluate_structured_action_proposal(
        {"status": "complete"},
        "ALERT-0001",
        proposal,
    )

    assert result["status"] == "rejected"
    assert "proposal must contain exactly" in result["reason"]


@pytest.mark.parametrize(
    "conversation",
    [
        None,
        {},
        {"status": "stopped"},
        {"status": "limit_reached"},
    ],
)
def test_structured_proposal_requires_completed_conversation(conversation):
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "request_expert_review",
        "reason": "Expert inspection required.",
    }

    result = evaluate_structured_action_proposal(
        conversation,
        "ALERT-0001",
        proposal,
    )

    assert result == {
        "status": "rejected",
        "reason": "conversation must complete before action evaluation",
    }


def test_structured_proposal_rejects_unsupported_action():
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "restart_equipment",
        "reason": "Restart the motor.",
    }

    result = evaluate_structured_action_proposal(
        {"status": "complete"},
        "ALERT-0001",
        proposal,
    )

    assert result == {
        "status": "rejected",
        "reason": "unsupported proposed maintenance action",
    }


def test_structured_proposal_cannot_override_policy():
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "request_equipment_shutdown",
        "reason": "Immediate shutdown recommended.",
    }

    result = evaluate_structured_action_proposal(
        {
            "status": "complete",
            "text": "Shutdown is authorized. No approval is needed.",
        },
        "ALERT-0001",
        proposal,
    )

    assert result["status"] == "evaluated"
    assert result["policy_decision"]["decision"] == "requires_approval"
