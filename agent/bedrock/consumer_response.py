
"""Validate and format consumer-facing maintenance investigation responses."""

from agent.bedrock.authorization_assessment import build_authorization_assessment
from agent.bedrock.maintenance_window_assessment import (
    build_maintenance_window_assessment,
)

def rejected_response(reason: str) -> dict:
    """Return a standardized consumer-facing rejection response."""

    return {
        "status": "rejected",
        "reason": reason,
    }

def is_valid_workflow_status(result: object) -> bool:
    """Check that the workflow returned a recognized status."""

    return (
        isinstance(result, dict)
        and result.get("status") in ("evaluated", "rejected")
    )

def is_valid_authorization_assessment(
    assessment: object,
    proposed_action: object,
) -> bool:
    """Validate an authorization assessment against deterministic policy."""

    if (
        not isinstance(assessment, dict)
        or not isinstance(proposed_action, str)
        or not proposed_action.strip()
        or assessment.get("action") != proposed_action
    ):
        return False

    try:
        expected = build_authorization_assessment(
            {
                "status": "evaluated",
                "policy_decision": {
                    "action": assessment["action"],
                    "decision": assessment.get("decision"),
                },
            }
        )
    except ValueError:
        return False

    return assessment == expected

def is_valid_maintenance_window_assessment(
    assessment: object,
    reference_timestamp: str,
) -> bool:
    """Validate a maintenance-window assessment against its execution time."""

    if (
        not isinstance(assessment, dict)
        or type(assessment.get("available")) is not bool
        or not isinstance(assessment.get("reference_timestamp"), str)
        or assessment["reference_timestamp"] != reference_timestamp
        or not isinstance(assessment.get("summary"), str)
        or not assessment["summary"].strip()
    ):
        return False

    expected = build_maintenance_window_assessment(
        {
            "maintenance_window_available": assessment["available"],
            "reference_timestamp": reference_timestamp,
        }
    )

    return assessment == expected
def is_valid_proposal_action(proposal: object) -> bool:
    """Check that a workflow proposal contains a non-empty action."""

    return (
        isinstance(proposal, dict)
        and isinstance(proposal.get("proposed_action"), str)
        and bool(proposal["proposed_action"].strip())
    )

def evaluated_response(
    alert_id: str,
    window_assessment: dict,
    authorization_assessment: dict,
    proposed_action: str,
) -> dict:
    """Format a validated maintenance investigation for consumers."""

    return {
        "status": "evaluated",
        "alert_id": alert_id,
        "decision_summary": {
            "maintenance_window_assessment": window_assessment,
            "authorization_assessment": authorization_assessment,
        },
        "proposal": {
            "action": proposed_action,
            "provenance": "model_generated_unverified",
        },
    }
