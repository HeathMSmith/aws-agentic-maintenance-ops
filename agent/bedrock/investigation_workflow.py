"""Coordinate Bedrock investigation, proposal generation, and policy evaluation."""

from agent.bedrock.converse_loop import run_conversation
from agent.bedrock.policy_gate import evaluate_structured_action_proposal
from agent.bedrock.proposal_generator import generate_action_proposal


def run_investigation_workflow(
    client,
    model_id: str,
    alert_id: str,
    execution_context: dict | None = None,
) -> dict:
    """Run an investigation and independently evaluate its proposed action."""

    if not isinstance(alert_id, str) or not alert_id.strip():
        return {
            "status": "rejected",
            "reason": "alert_id must be a non-empty string",
        }

    investigation = run_conversation(
        client=client,
        model_id=model_id,
        prompt=f"Investigate equipment alert {alert_id}.",
        execution_context=execution_context,
    )

    if investigation["status"] != "complete":
        return {
            "status": "rejected",
            "reason": "investigation did not complete",
            "investigation": investigation,
        }

    proposal_result = generate_action_proposal(
        client=client,
        model_id=model_id,
        investigation_result=investigation,
        alert_id=alert_id,
    )

    if proposal_result["status"] != "proposed":
        return {
            "status": "rejected",
            "reason": "valid structured action proposal was not received",
            "proposal_result": proposal_result,
        }

    policy_result = evaluate_structured_action_proposal(
        conversation_result=investigation,
        expected_alert_id=alert_id,
        proposal=proposal_result["proposal"],
    )

    return {
        "status": (
            "evaluated"
            if policy_result["status"] == "evaluated"
            else "rejected"
        ),
        "investigation": investigation,
        "proposal": proposal_result["proposal"],
        "policy_result": policy_result,
    }
