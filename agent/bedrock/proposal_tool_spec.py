"""Bedrock tool configuration for structured maintenance-action proposals."""

from agent.bedrock.proposal_response import PROPOSAL_TOOL_NAME


PROPOSAL_TOOL = {
    "toolSpec": {
        "name": PROPOSAL_TOOL_NAME,
        "description": (
            "Submit exactly one structured maintenance-action proposal "
            "for application-side validation and policy evaluation. "
            "Submitting a proposal does not authorize or execute an action."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "Identifier of the investigated alert.",
                    },
                    "proposed_action": {
                        "type": "string",
                        "description": "Proposed maintenance action.",
                        "enum": [
                            "continue_monitoring",
                            "request_expert_review",
                            "create_maintenance_work_order",
                            "request_equipment_shutdown",
                        ],
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "Brief evidence-based explanation for the proposal. "
                            "Do not claim that approval has been granted."
                        ),
                    },
                },
                "required": [
                    "alert_id",
                    "proposed_action",
                    "reason",
                ],
                "additionalProperties": False,
            }
        },
    }
}


PROPOSAL_TOOL_CONFIG = {
    "tools": [PROPOSAL_TOOL],
    "toolChoice": {
        "tool": {
            "name": PROPOSAL_TOOL_NAME,
        }
    },
}
