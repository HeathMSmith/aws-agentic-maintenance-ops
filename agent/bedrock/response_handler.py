"""Interpret Bedrock Converse API responses."""

from agent.bedrock.tool_results import build_tool_result_message


def handle_converse_response(
    response: dict,
    execution_context: dict | None = None,
) -> dict:
    """Extract model text or execute requested read-only tools."""

    stop_reason = response["stopReason"]
    message = response["output"]["message"]

    if stop_reason == "end_turn":
        text = "\n".join(
            block["text"]
            for block in message["content"]
            if "text" in block
        )

        return {
            "status": "complete",
            "text": text,
        }

    if stop_reason == "tool_use":
        tool_messages = [
            build_tool_result_message(
                block["toolUse"],
                execution_context=execution_context,
            )
            for block in message["content"]
            if "toolUse" in block
        ]

        return {
            "status": "tool_results",
            "messages": tool_messages,
        }

    return {
        "status": "unexpected_stop",
        "reason": stop_reason,
    }
