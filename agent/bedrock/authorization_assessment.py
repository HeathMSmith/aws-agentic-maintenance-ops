
"""Build deterministic maintenance authorization assessments."""


def build_authorization_assessment(policy_result: dict) -> dict:
    """Describe a successfully evaluated maintenance policy decision."""

    if not isinstance(policy_result, dict):
        raise ValueError("policy_result must be a dictionary")

    if policy_result.get("status") != "evaluated":
        raise ValueError("policy evaluation must be successful")

    policy_decision = policy_result.get("policy_decision")
    if not isinstance(policy_decision, dict):
        raise ValueError("policy_decision must be a dictionary")

    action = policy_decision.get("action")
    decision = policy_decision.get("decision")

    summaries = {
        ("request_equipment_shutdown", "requires_approval"): (
            "The proposed equipment shutdown requires approval "
            "before execution."
        ),
        ("request_expert_review", "permitted"): (
            "The proposed expert review request is permitted "
            "under the simulation policy."
        ),
        ("continue_monitoring", "requires_approval"): (
            "The proposed continuation of monitoring requires "
            "approval under the simulation policy."
        ),
        ("continue_monitoring", "permitted"): (
            "The proposed continuation of monitoring is permitted "
            "under the simulation policy."
        ),
        ("create_maintenance_work_order", "requires_approval"): (
            "The proposed maintenance work order requires approval "
            "before execution."
        ),
    }

    try:
        summary = summaries[(action, decision)]
    except (KeyError, TypeError):
        raise ValueError("unsupported authorization assessment") from None

    return {
        "action": action,
        "decision": decision,
        "summary": summary,
    }
