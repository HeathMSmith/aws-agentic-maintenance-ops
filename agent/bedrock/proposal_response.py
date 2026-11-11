"""Extract structured maintenance-action proposals from Bedrock responses."""

from agent.bedrock.action_proposal import validate_action_proposal


PROPOSAL_TOOL_NAME = "submit_maintenance_action_proposal"


def extract_action_proposal(response: dict) -> dict:
    """Extract and validate one proposed maintenance action."""

    if not isinstance(response, dict):
        return {
            "status": "rejected",
            "reason": "invalid Bedrock response",
        }

    if response.get("stopReason") != "tool_use":
        return {
            "status": "rejected",
            "reason": "model did not submit an action proposal",
        }

    output = response.get("output")

    if not isinstance(output, dict):
        return {
            "status": "rejected",
            "reason": "invalid proposal response structure",
        }

    message = output.get("message")

    if not isinstance(message, dict):
        return {
            "status": "rejected",
            "reason": "invalid proposal response structure",
        }

    content = message.get("content", [])

    if not isinstance(content, list):
        return {
            "status": "rejected",
            "reason": "invalid proposal response content",
        }

    tool_requests = [
        block["toolUse"]
        for block in content
        if isinstance(block, dict) and "toolUse" in block
    ]

    if len(tool_requests) != 1:
        return {
            "status": "rejected",
            "reason": "expected exactly one action proposal",
        }

    tool_request = tool_requests[0]

    if (
        not isinstance(tool_request, dict)
        or tool_request.get("name") != PROPOSAL_TOOL_NAME
    ):
        return {
            "status": "rejected",
            "reason": "unexpected proposal tool",
        }

    validation = validate_action_proposal(tool_request.get("input"))

    if not validation["valid"]:
        return {
            "status": "rejected",
            "reason": validation["reason"],
        }

    return {
        "status": "proposed",
        "proposal": validation["proposal"],
    }