"""Coordinate Bedrock investigation, proposal generation, and policy evaluation."""

from agent.bedrock.converse_loop import run_conversation
from agent.bedrock.policy_gate import evaluate_structured_action_proposal
from agent.bedrock.proposal_generator import generate_action_proposal
from agent.bedrock.evidence_completeness import validate_evidence_completeness
from agent.bedrock.evidence_identity import validate_evidence_identity
from agent.bedrock.investigation_prompt import build_investigation_prompt
from agent.bedrock.operational_facts import extract_maintenance_window_facts


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
        prompt=build_investigation_prompt(alert_id),
        execution_context=execution_context,
    )

    if investigation["status"] != "complete":
        return {
            "status": "rejected",
            "reason": "investigation did not complete",
            "investigation": investigation,
        }
    evidence_validation = validate_evidence_completeness(
        investigation.get("execution_trace")
    )

    if not evidence_validation["valid"]:
        return {
            "status": "rejected",
            "reason": "investigation evidence is incomplete",
            "evidence_validation": evidence_validation,
            "investigation": investigation,
        }
    identity_validation = validate_evidence_identity(
        execution_trace=investigation.get("execution_trace"),
        alert_id=alert_id,
    )

    if not identity_validation["valid"]:
        return {
            "status": "rejected",
            "reason": "investigation evidence identity is invalid",
            "identity_validation": identity_validation,
            "investigation": investigation,
        }

    operational_facts_validation = extract_maintenance_window_facts(
        evidence_records=investigation.get("evidence_records"),
        expected_asset_id=identity_validation["asset_id"],
        execution_context=investigation.get("execution_context"),
    )

    if not operational_facts_validation["valid"]:
        return {
            "status": "rejected",
            "reason": "investigation operational facts are invalid",
            "operational_facts_validation": operational_facts_validation,
            "investigation": investigation,
        }

    proposal_result = generate_action_proposal(
        client=client,
        model_id=model_id,
        investigation_result=investigation,
        alert_id=alert_id,
        operational_facts=operational_facts_validation["facts"],
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
            "evaluated" if policy_result["status"] == "evaluated" else "rejected"
        ),
        "investigation": investigation,
        "proposal": proposal_result["proposal"],
        "policy_result": policy_result,
    }
