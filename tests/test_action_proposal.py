import pytest

from agent.bedrock.action_proposal import validate_action_proposal


@pytest.mark.parametrize(
    "action",
    [
        "continue_monitoring",
        "request_expert_review",
        "create_maintenance_work_order",
        "request_equipment_shutdown",
    ],
)
def test_valid_action_proposal(action):
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": action,
        "reason": "Equipment anomaly requires assessment.",
    }

    result = validate_action_proposal(proposal)

    assert result["valid"] is True
    assert result["proposal"] == proposal


@pytest.mark.parametrize(
    "proposal",
    [
        None,
        "request_expert_review",
        [],
        123,
    ],
)
def test_non_dictionary_proposal_rejected(proposal):
    result = validate_action_proposal(proposal)

    assert result == {
        "valid": False,
        "reason": "proposal must be a dictionary",
    }


@pytest.mark.parametrize(
    "proposal",
    [
        {},
        {"alert_id": "ALERT-0001"},
        {
            "alert_id": "ALERT-0001",
            "proposed_action": "request_expert_review",
        },
        {
            "alert_id": "ALERT-0001",
            "proposed_action": "request_expert_review",
            "reason": "Expert inspection required.",
            "approved": True,
        },
    ],
)
def test_incorrect_proposal_fields_rejected(proposal):
    result = validate_action_proposal(proposal)

    assert result["valid"] is False
    assert result["reason"].startswith("proposal must contain exactly")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alert_id", ""),
        ("alert_id", None),
        ("alert_id", 123),
        ("proposed_action", ""),
        ("proposed_action", None),
        ("proposed_action", 123),
        ("reason", ""),
        ("reason", "   "),
        ("reason", None),
        ("reason", 123),
    ],
)
def test_invalid_field_values_rejected(field, value):
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "request_expert_review",
        "reason": "Expert inspection required.",
    }

    proposal[field] = value

    result = validate_action_proposal(proposal)

    assert result["valid"] is False
    assert result["reason"] == f"{field} must be a non-empty string"


def test_unsupported_action_rejected():
    proposal = {
        "alert_id": "ALERT-0001",
        "proposed_action": "restart_equipment",
        "reason": "Restart the motor.",
    }

    result = validate_action_proposal(proposal)

    assert result == {
        "valid": False,
        "reason": "unsupported proposed maintenance action",
    }
