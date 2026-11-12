"""Coordinate a bounded Bedrock Converse tool-use workflow."""

from agent.bedrock.execution_context import create_execution_context
from agent.bedrock.response_handler import handle_converse_response
from agent.bedrock.tool_specs import TOOL_CONFIG
from agent.bedrock.evidence_record import build_evidence_record


def run_conversation(
    client,
    model_id: str,
    prompt: str,
    max_model_calls: int = 4,
    execution_context: dict | None = None,
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

    execution_trace = []
    evidence_records = []

    if execution_context is None:
        execution_context = create_execution_context()
    else:
        execution_context = create_execution_context(
            execution_context["reference_timestamp"]
    )

    for model_call_number in range(1, max_model_calls + 1):
        response = client.converse(
            modelId=model_id,
            messages=messages,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": 2048},
        )

        result = handle_converse_response(
            response,
            execution_context=execution_context,
        )

        if result["status"] == "complete":
            return {
                "status": "complete",
                "text": result["text"],
                "model_calls": model_call_number,
                "execution_context": execution_context,
                "execution_trace": execution_trace,
                "evidence_records": evidence_records,
            }

        if result["status"] == "unexpected_stop":
            return {
                "status": "stopped",
                "reason": result["reason"],
                "execution_trace": execution_trace,
                "evidence_records": evidence_records,
            }

        # Preserve the original assistant tool-use request.
        messages.append(response["output"]["message"])

        # Return all tool results together in one user message.
        tool_results = [
            block for message in result["messages"] for block in message["content"]
        ]

        tool_requests = [
            block["toolUse"]
            for block in response["output"]["message"]["content"]
            if "toolUse" in block
        ]

        for tool_request, tool_result in zip(tool_requests, tool_results):
            tool_input = tool_request.get("input", {})

            identifiers = {}

            if isinstance(tool_input, dict):
                for field in ("alert_id", "asset_id"):
                    value = tool_input.get(field)

                    if isinstance(value, str) and value.strip():
                        identifiers[field] = value

            execution_trace.append(
                {
                    "model_call": model_call_number,
                    "tool_name": tool_request["name"],
                    "status": tool_result["toolResult"]["status"],
                    "identifiers": identifiers,
                }
            )

            evidence_tools = {
                "get_equipment_alert",
                "get_asset_context",
                "get_maintenance_history",
                "get_production_schedule",
                "get_maintenance_window_status",
            }

            tool_name = tool_request["name"]
            validated_result = tool_result["toolResult"]

            if (
                tool_name in evidence_tools
                and validated_result["status"] == "success"
            ):
                evidence_records.append(
                    build_evidence_record(
                        tool_name=tool_name,
                        tool_use_id=tool_request["toolUseId"],
                        identifiers=identifiers,
                        result=validated_result["content"][0]["json"],
                    )
                )

        if not tool_results:
            return {
                "status": "stopped",
                "reason": "tool_use response contained no tool requests",
                "execution_trace": execution_trace,
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
        "execution_trace": execution_trace,
        "evidence_records": evidence_records,
    }
