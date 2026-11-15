
"""AWS Lambda entry point for simulated maintenance investigations."""

from agent.bedrock.consumer_response import (
    evaluated_response,
    is_valid_authorization_assessment,
    is_valid_maintenance_window_assessment,
    is_valid_proposal_action,
    is_valid_workflow_status,
    rejected_response,
)
from agent.bedrock.execution_context import create_execution_context
from agent.bedrock.investigation_workflow import run_investigation_workflow
from agent.bedrock.live_client import create_bedrock_runtime_client


MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


def lambda_handler(event: dict, context) -> dict:
    """Validate a direct Lambda investigation invocation."""

    if not isinstance(event, dict):
        return {
            "status": "rejected",
            "reason": "invalid_invocation_input",
        }

    alert_id = event.get("alert_id")

    if not isinstance(alert_id, str) or not alert_id.strip():
        return {
            "status": "rejected",
            "reason": "invalid_invocation_input",
        }

    if "reference_timestamp" in event:
        reference_timestamp = event["reference_timestamp"]

        if reference_timestamp is None:
            return {
                "status": "rejected",
                "reason": "invalid_invocation_input",
            }
    else:
        reference_timestamp = None

    try:
        execution_context = create_execution_context(reference_timestamp)
    except ValueError:
        return {
            "status": "rejected",
            "reason": "invalid_invocation_input",
        }

    client = create_bedrock_runtime_client()

    result = run_investigation_workflow(
        client=client,
        model_id=MODEL_ID,
        alert_id=alert_id,
        execution_context=execution_context,
    )

    if not is_valid_workflow_status(result):
        return rejected_response("invalid_workflow_result")

    if result["status"] != "evaluated":
        return rejected_response("investigation_failed")

    window_assessment = result.get("maintenance_window_assessment")
    authorization_assessment = result.get("authorization_assessment")
    proposal = result.get("proposal")

    if not is_valid_proposal_action(proposal):
        return rejected_response("invalid_workflow_result")

    if not is_valid_authorization_assessment(
        authorization_assessment,
        proposal["proposed_action"],
    ):
        return rejected_response("invalid_workflow_result")

    if not is_valid_maintenance_window_assessment(
        window_assessment,
        execution_context["reference_timestamp"],
    ):
        return rejected_response("invalid_workflow_result")


    return evaluated_response(
        alert_id=alert_id,
        window_assessment=window_assessment,
        authorization_assessment=authorization_assessment,
        proposed_action=proposal["proposed_action"],
    )
