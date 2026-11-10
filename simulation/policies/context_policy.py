from simulation.policies.maintenance_policy import evaluate_maintenance_action
from simulation.policies.evidence_validation import validate_investigation_evidence


def evaluate_action_with_context(action: str, investigation: dict) -> dict:
    """Evaluate a proposed action using incident investigation context."""

    classification = evaluate_maintenance_action(action)

    if classification["decision"] == "rejected":
        return classification

    validation = validate_investigation_evidence(investigation)

    if not validation["valid"]:
        return {
            "decision": "rejected",
            "reason": validation["reason"],
        }

    alert = investigation["alert"]
    asset = investigation["asset"]
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
