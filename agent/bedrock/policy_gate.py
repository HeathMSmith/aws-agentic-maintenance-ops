"""Apply deterministic policy checks to completed investigations."""

from agent.tools.maintenance_action_evaluation import (
    evaluate_proposed_maintenance_action,
)
from agent.bedrock.action_proposal import validate_action_proposal


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

def evaluate_structured_action_proposal(
    conversation_result: dict,
    expected_alert_id: str,
    proposal: dict,
) -> dict:
    """Validate a model proposal and independently evaluate its action."""

    if (
        not isinstance(conversation_result, dict)
        or conversation_result.get("status") != "complete"
    ):
        return {
            "status": "rejected",
            "reason": "conversation must complete before action evaluation",
        }

    validation = validate_action_proposal(proposal)

    if not validation["valid"]:
        return {
            "status": "rejected",
            "reason": validation["reason"],
        }

    validated_proposal = validation["proposal"]

    if validated_proposal["alert_id"] != expected_alert_id:
        return {
            "status": "rejected",
            "reason": "proposal alert_id does not match the requested incident",
        }

    return evaluate_conversation_action(
        conversation_result=conversation_result,
        alert_id=expected_alert_id,
        proposed_action=validated_proposal["proposed_action"],
    )
