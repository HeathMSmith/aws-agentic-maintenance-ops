"""Validate structured maintenance-action proposals."""

from simulation.policies.maintenance_policy import ALLOWED_ACTIONS


def validate_action_proposal(proposal: dict) -> dict:
    """Validate a structured proposal without authorizing its action."""

    if not isinstance(proposal, dict):
        return {
            "valid": False,
            "reason": "proposal must be a dictionary",
        }

    required_fields = {"alert_id", "proposed_action", "reason"}

    if set(proposal) != required_fields:
        return {
            "valid": False,
            "reason": "proposal must contain exactly alert_id, proposed_action, and reason",
        }

    for field in required_fields:
        value = proposal[field]

        if not isinstance(value, str) or not value.strip():
            return {
                "valid": False,
                "reason": f"{field} must be a non-empty string",
            }

    if proposal["proposed_action"] not in ALLOWED_ACTIONS:
        return {
            "valid": False,
            "reason": "unsupported proposed maintenance action",
        }

    return {
        "valid": True,
        "proposal": {
            "alert_id": proposal["alert_id"],
            "proposed_action": proposal["proposed_action"],
            "reason": proposal["reason"],
        },
    }
