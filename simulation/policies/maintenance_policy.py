ALLOWED_ACTIONS = {
    "continue_monitoring": "permitted",
    "request_expert_review": "permitted",
    "create_maintenance_work_order": "requires_approval",
    "request_equipment_shutdown": "requires_approval",
}


def evaluate_maintenance_action(action: str) -> dict:
    """Classify a proposed maintenance action against simulation policy."""

    if not isinstance(action, str) or not action.strip():
        return {
            "decision": "rejected",
            "reason": "action must be a non-empty string",
        }

    if action not in ALLOWED_ACTIONS:
        return {
            "decision": "rejected",
            "reason": f"Unsupported maintenance action: {action}",
        }

    return {
        "action": action,
        "decision": ALLOWED_ACTIONS[action],
    }
