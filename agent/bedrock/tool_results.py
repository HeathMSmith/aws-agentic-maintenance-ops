"""Build Converse API messages from local tool execution results."""

from agent.bedrock.tool_dispatcher import dispatch_tool
from agent.bedrock.evidence_result import validate_evidence_result
from agent.bedrock.tool_specs import TOOL_CONFIG


def build_tool_result_message(
    tool_use: dict,
    execution_context: dict | None = None,
) -> dict:
    """Execute a requested tool and return a Converse-compatible user message."""

    tool_use_id = tool_use["toolUseId"]
    tool_name = tool_use["name"]
    tool_input = tool_use["input"]

    allowed_tools = {
        tool["toolSpec"]["name"]
        for tool in TOOL_CONFIG["tools"]
    }

    if tool_name not in allowed_tools:
        result = {
            "error": "unsupported_tool",
            "message": (
                f"Tool '{tool_name}' is not allowed during investigation"
            ),
        }
    else:
        result = dispatch_tool(
            tool_name,
            tool_input,
            execution_context,
        )

    status = "error" if "error" in result else "success"

    evidence_tools = {
        "get_equipment_alert",
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }

    if tool_name in evidence_tools and status == "success":
        validation = validate_evidence_result(
            tool_name=tool_name,
            tool_input=tool_input,
            result=result,
        )

        if not validation["valid"]:
            status = "error"
            result = {
                "error": "invalid_evidence_result",
                "message": validation["reason"],
            }

    return {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [
                        {
                            "json": result,
                        }
                    ],
                    "status": status,
                }
            }
        ],
    }
