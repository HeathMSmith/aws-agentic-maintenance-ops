"""Apply deterministic policy checks to completed investigations."""

from agent.tools.maintenance_action_evaluation import (
    evaluate_proposed_maintenance_action,
)


def evaluate_conversation_action(
    conversation_result: dict,
    alert_id: str,
    proposed_action: str,
) -> dict:
    """Evaluate a structured action independently of model-generated text."""

    if (
        not isinstance(conversation_result, dict)
        or conversation_result.get("status") != "complete"
    ):
        return {
            "status": "rejected",
            "reason": "conversation must complete before action evaluation",
        }

    evaluation = evaluate_proposed_maintenance_action(
        alert_id,
        proposed_action,
    )

    if "error" in evaluation:
        return {
            "status": "rejected",
            "reason": evaluation["error"],
        }

    decision = evaluation["policy_decision"]

    return {
        "status": "evaluated",
        "alert_id": evaluation["alert_id"],
        "asset_id": evaluation["asset_id"],
        "proposed_action": evaluation["action"],
        "policy_decision": decision,
    }
