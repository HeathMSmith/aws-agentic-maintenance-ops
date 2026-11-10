"""Dispatch approved Bedrock tool requests to local Python functions."""

from agent.tools.equipment_alert import get_equipment_alert
from agent.tools.asset_context import get_asset_context
from agent.tools.maintenance_history import get_maintenance_history
from agent.tools.production_schedule import get_production_schedule
import logging

logger = logging.getLogger(__name__)


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Validate and execute an approved read-only tool."""

    if tool_name == "get_production_schedule":
        if (
            not isinstance(tool_input, dict)
            or set(tool_input) != {"asset_id"}
            or not isinstance(tool_input["asset_id"], str)
            or not tool_input["asset_id"].strip()
        ):
            return {
                "error": "invalid_tool_input",
                "message": (
                    "get_production_schedule requires a non-empty asset_id string"
                ),
            }

        result = get_production_schedule(tool_input["asset_id"])

        logger.info(
            "Tool execution completed: tool=%s status=%s",
            tool_name,
            "error" if "error" in result else "success",
        )

        return result

    if tool_name == "get_maintenance_history":
        if (
            not isinstance(tool_input, dict)
            or set(tool_input) != {"asset_id"}
            or not isinstance(tool_input["asset_id"], str)
            or not tool_input["asset_id"].strip()
        ):
            return {
                "error": "invalid_tool_input",
                "message": (
                    "get_maintenance_history requires a non-empty asset_id string"
                ),
            }

        result = get_maintenance_history(tool_input["asset_id"])

        logger.info(
            "Tool execution completed: tool=%s status=%s",
            tool_name,
            "error" if "error" in result else "success",
        )

        return result

    if tool_name == "get_asset_context":
        if (
            not isinstance(tool_input, dict)
            or set(tool_input) != {"asset_id"}
            or not isinstance(tool_input["asset_id"], str)
            or not tool_input["asset_id"].strip()
        ):
            return {
                "error": "invalid_tool_input",
                "message": ("get_asset_context requires a non-empty asset_id string"),
            }

        result = get_asset_context(tool_input["asset_id"])

        logger.info(
            "Tool execution completed: tool=%s status=%s",
            tool_name,
            "error" if "error" in result else "success",
        )

        return result

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

    result = get_equipment_alert(tool_input["alert_id"])

    logger.info(
        "Tool execution completed: tool=%s status=%s",
        tool_name,
        "error" if "error" in result else "success",
    )

    return result
