"""Generate structured maintenance-action proposals using Bedrock Converse."""

import json
import logging

from agent.bedrock.proposal_response import extract_action_proposal
from agent.bedrock.proposal_tool_spec import PROPOSAL_TOOL_CONFIG

logger = logging.getLogger(__name__)


def generate_action_proposal(
    client,
    model_id: str,
    investigation_result: dict,
    alert_id: str,
    operational_facts: dict | None = None,
) -> dict:
    """Request one structured proposal from a completed investigation."""

    if (
        not isinstance(investigation_result, dict)
        or investigation_result.get("status") != "complete"
    ):
        return {
            "status": "rejected",
            "reason": "investigation must complete before proposal generation",
        }

    if not isinstance(alert_id, str) or not alert_id.strip():
        return {
            "status": "rejected",
            "reason": "alert_id must be a non-empty string",
        }

    facts_section = ""

    if operational_facts is not None:
        facts_section = (
            "\n\nValidated operational facts:\n"
            f"{json.dumps(operational_facts, sort_keys=True)}\n"
            "These scheduling facts were validated by the application. "
            "Use them as authoritative for the investigation reference time. "
            "Do not describe an unavailable maintenance window as upcoming."
        )

    prompt = (
        f"Investigation for alert {alert_id}:\n\n"
        f"{investigation_result.get('text', '')}"
        f"{facts_section}\n\n"
        "Submit exactly one maintenance-action proposal using the "
        "provided tool. Base the proposal on the investigation evidence. "
        "Do not claim that maintenance or shutdown approval has been granted."
    )

    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            toolConfig=PROPOSAL_TOOL_CONFIG,
            inferenceConfig={"maxTokens": 1024},
        )
    except Exception:
        logger.exception(
            "Bedrock Converse request failed during maintenance proposal generation"
        )
        return {
            "status": "rejected",
            "reason": "bedrock_request_failed",
        }

    return extract_action_proposal(response)
