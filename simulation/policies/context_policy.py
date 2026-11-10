from simulation.policies.maintenance_policy import evaluate_maintenance_action


def evaluate_action_with_context(action: str, investigation: dict) -> dict:
    """Evaluate a proposed action using incident investigation context."""

    classification = evaluate_maintenance_action(action)

    if classification["decision"] == "rejected":
        return classification

    if not isinstance(investigation, dict):
        return {
            "decision": "rejected",
            "reason": "investigation must be a dictionary",
        }

    if investigation.get("status") != "investigated":
        return {
            "decision": "rejected",
            "reason": "investigation is incomplete",
        }

    alert = investigation.get("alert")
    asset = investigation.get("asset")

    if not isinstance(alert, dict) or not isinstance(asset, dict):
        return {
            "decision": "rejected",
            "reason": "required incident evidence is missing",
        }

    severity = alert.get("severity")
    criticality = asset.get("criticality")

    if severity not in {"info", "warning", "critical"}:
        return {
            "decision": "rejected",
            "reason": "invalid or missing alert severity",
        }

    if criticality not in {"low", "medium", "high"}:
        return {
            "decision": "rejected",
            "reason": "invalid or missing asset criticality",
        }

    if (
        action == "continue_monitoring"
        and criticality == "high"
        and severity in {"warning", "critical"}
    ):
        return {
            "action": action,
            "decision": "requires_approval",
            "reason": "High-criticality asset requires expert review",
        }

    return classification
