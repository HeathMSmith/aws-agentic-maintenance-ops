import pytest

from simulation.policies.maintenance_policy import evaluate_maintenance_action


@pytest.mark.parametrize(
    "action",
    [
        "continue_monitoring",
        "request_expert_review",
    ],
)
def test_permitted_actions(action):
    result = evaluate_maintenance_action(action)

    assert result == {
        "action": action,
        "decision": "permitted",
    }


@pytest.mark.parametrize(
    "action",
    [
        "create_maintenance_work_order",
        "request_equipment_shutdown",
    ],
)
def test_actions_requiring_approval(action):
    result = evaluate_maintenance_action(action)

    assert result == {
        "action": action,
        "decision": "requires_approval",
    }


def test_unsupported_action():
    result = evaluate_maintenance_action("restart_motor")

    assert result == {
        "decision": "rejected",
        "reason": "Unsupported maintenance action: restart_motor",
    }


@pytest.mark.parametrize("action", ["", "   ", None, 123])
def test_invalid_action_input(action):
    result = evaluate_maintenance_action(action)

    assert result == {
        "decision": "rejected",
        "reason": "action must be a non-empty string",
    }
