"""Dispatch approved Bedrock tool requests to local Python functions."""

import logging

from agent.tools.asset_context import get_asset_context
from agent.tools.equipment_alert import get_equipment_alert
from agent.tools.maintenance_history import get_maintenance_history
from agent.tools.production_schedule import get_production_schedule


logger = logging.getLogger(__name__)


# Explicit allowlist of executable read-only tools.
TOOL_REGISTRY = {
    "get_equipment_alert": (get_equipment_alert, "alert_id"),
    "get_asset_context": (get_asset_context, "asset_id"),
    "get_maintenance_history": (get_maintenance_history, "asset_id"),
    "get_production_schedule": (get_production_schedule, "asset_id"),
}


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Validate and execute an approved read-only tool."""

    if tool_name not in TOOL_REGISTRY:
        return {
            "error": "unsupported_tool",
            "message": f"Tool '{tool_name}' is not allowed",
        }

    tool_function, required_argument = TOOL_REGISTRY[tool_name]

    if (
        not isinstance(tool_input, dict)
        or set(tool_input) != {required_argument}
        or not isinstance(tool_input[required_argument], str)
        or not tool_input[required_argument].strip()
    ):
        return {
            "error": "invalid_tool_input",
            "message": (
                f"{tool_name} requires a non-empty "
                f"{required_argument} string"
            ),
        }

    result = tool_function(tool_input[required_argument])

    logger.info(
        "Tool execution completed: tool=%s status=%s",
        tool_name,
        "error" if "error" in result else "success",
    )

    return result
