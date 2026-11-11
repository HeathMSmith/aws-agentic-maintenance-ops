"""Evaluate proposed maintenance actions against deterministic policy."""

from simulation.investigate_incident import investigate_incident
from simulation.policies.context_policy import evaluate_action_with_context


def evaluate_proposed_maintenance_action(
    alert_id: str,
    action: str,
) -> dict:
    """Evaluate a proposed action using validated incident evidence."""

    if not isinstance(alert_id, str) or not alert_id.strip():
        return {"error": "alert_id must be a non-empty string"}

    if not isinstance(action, str) or not action.strip():
        return {"error": "action must be a non-empty string"}

    investigation = investigate_incident(alert_id)

    if investigation["status"] != "investigated":
        return {
            "error": "investigation_failed",
            "message": investigation.get("error", "Investigation failed"),
        }

    decision = evaluate_action_with_context(action, investigation)

    return {
        "alert_id": alert_id,
        "asset_id": investigation["alert"]["asset_id"],
        "action": action,
        "policy_decision": decision,
    }
