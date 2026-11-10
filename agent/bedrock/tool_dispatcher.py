"""Dispatch approved Bedrock tool requests to local Python functions."""

from agent.tools.equipment_alert import get_equipment_alert


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Validate and execute an approved read-only tool."""

    if tool_name != "get_equipment_alert":
        return {
            "error": "unsupported_tool",
            "message": f"Tool '{tool_name}' is not allowed",
        }

    if (
        not isinstance(tool_input, dict)
        or set(tool_input) != {"alert_id"}
        or not isinstance(tool_input["alert_id"], str)
        or not tool_input["alert_id"].strip()
    ):
        return {
            "error": "invalid_tool_input",
            "message": "get_equipment_alert requires a non-empty alert_id string",
        }

    return get_equipment_alert(tool_input["alert_id"])
