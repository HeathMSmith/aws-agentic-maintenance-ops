"""Coordinate a bounded Bedrock Converse tool-use workflow."""

from agent.bedrock.response_handler import handle_converse_response
from agent.bedrock.tool_specs import TOOL_CONFIG


def run_conversation(
    client,
    model_id: str,
    prompt: str,
    max_model_calls: int = 4,
) -> dict:
    """Run a bounded model conversation with read-only tool execution."""

    if type(max_model_calls) is not int or max_model_calls < 1:
        raise ValueError("max_model_calls must be a positive integer")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]

    for _ in range(max_model_calls):
        response = client.converse(
            modelId=model_id,
            messages=messages,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": 512},
        )

        result = handle_converse_response(response)

        if result["status"] == "complete":
            return {
                "status": "complete",
                "text": result["text"],
                "model_calls": len(
                    [message for message in messages if message["role"] == "assistant"]
                ) + 1,
            }

        if result["status"] == "unexpected_stop":
            return {
                "status": "stopped",
                "reason": result["reason"],
            }

        # Preserve the original assistant tool-use request.
        messages.append(response["output"]["message"])

        # Return all tool results together in one user message.
        tool_results = [
            block
            for message in result["messages"]
            for block in message["content"]
        ]

        if not tool_results:
            return {
                "status": "stopped",
                "reason": "tool_use response contained no tool requests",
            }

        messages.append(
            {
                "role": "user",
                "content": tool_results,
            }
        )

    return {
        "status": "limit_reached",
        "reason": "maximum model calls reached",
    }
