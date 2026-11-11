import pytest

from agent.tools.maintenance_action_evaluation import (
    evaluate_proposed_maintenance_action,
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
def test_supported_maintenance_actions(action, expected_decision):
    result = evaluate_proposed_maintenance_action(
        "ALERT-0001",
        action,
    )

    assert result["alert_id"] == "ALERT-0001"
    assert result["asset_id"] == "CONV-MTR-042"
    assert result["action"] == action
    assert result["policy_decision"]["decision"] == expected_decision


@pytest.mark.parametrize(
    "alert_id",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_invalid_alert_id(alert_id):
    result = evaluate_proposed_maintenance_action(
        alert_id,
        "request_expert_review",
    )

    assert result == {
        "error": "alert_id must be a non-empty string"
    }


@pytest.mark.parametrize(
    "action",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_invalid_action(action):
    result = evaluate_proposed_maintenance_action(
        "ALERT-0001",
        action,
    )

    assert result == {
        "error": "action must be a non-empty string"
    }


def test_unsupported_maintenance_action():
    result = evaluate_proposed_maintenance_action(
        "ALERT-0001",
        "restart_equipment",
    )

    assert result["policy_decision"]["decision"] == "rejected"
    assert "Unsupported maintenance action" in (
        result["policy_decision"]["reason"]
    )


def test_unknown_alert():
    result = evaluate_proposed_maintenance_action(
        "UNKNOWN-ALERT",
        "request_expert_review",
    )

    assert result["error"] == "investigation_failed"
    assert "message" in result
