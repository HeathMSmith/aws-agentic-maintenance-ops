"""Dispatch approved Bedrock tool requests to local Python functions."""

import logging

from agent.tools.asset_context import get_asset_context
from agent.tools.equipment_alert import get_equipment_alert
from agent.tools.maintenance_history import get_maintenance_history
from agent.tools.production_schedule import get_production_schedule
from agent.tools.maintenance_window_status import get_maintenance_window_status
from simulation.clock import parse_simulation_time
from agent.tools.maintenance_action_evaluation import (
    evaluate_proposed_maintenance_action,
)


logger = logging.getLogger(__name__)


# Explicit allowlist of executable read-only tools.
TOOL_REGISTRY = {
    "get_equipment_alert": (get_equipment_alert, "alert_id"),
    "get_asset_context": (get_asset_context, "asset_id"),
    "get_maintenance_history": (get_maintenance_history, "asset_id"),
    "get_production_schedule": (get_production_schedule, "asset_id"),
}


def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    execution_context: dict | None = None,
) -> dict:
    """Validate and execute an approved read-only tool."""

    if tool_name == "get_maintenance_window_status":
        if (
            not isinstance(tool_input, dict)
            or set(tool_input) != {"asset_id"}
            or not isinstance(tool_input["asset_id"], str)
            or not tool_input["asset_id"].strip()
        ):
            return {
                "error": "invalid_tool_input",
                "message": (
                    "get_maintenance_window_status requires "
                    "a non-empty asset_id string"
                ),
            }

        if (
            not isinstance(execution_context, dict)
            or "reference_timestamp" not in execution_context
        ):
            return {
                "error": "missing_execution_context",
                "message": "A trusted reference_timestamp is required",
            }

        reference_timestamp = execution_context["reference_timestamp"]

        try:
            parse_simulation_time(reference_timestamp)
        except ValueError:
            return {
                "error": "invalid_execution_context",
                "message": "reference_timestamp must be a timezone-aware ISO 8601 timestamp",
            }

        result = get_maintenance_window_status(
            tool_input["asset_id"],
            reference_timestamp,
        )

        logger.info(
            "Tool execution completed: tool=%s status=%s",
            tool_name,
            "error" if "error" in result else "success",
        )

        return result
    if tool_name == "evaluate_proposed_maintenance_action":
        if (
            not isinstance(tool_input, dict)
            or set(tool_input) != {"alert_id", "action"}
            or not isinstance(tool_input["alert_id"], str)
            or not tool_input["alert_id"].strip()
            or not isinstance(tool_input["action"], str)
            or not tool_input["action"].strip()
        ):
            return {
                "error": "invalid_tool_input",
                "message": (
                    "evaluate_proposed_maintenance_action requires "
                    "non-empty alert_id and action strings"
                ),
            }

        result = evaluate_proposed_maintenance_action(
            tool_input["alert_id"],
            tool_input["action"],
        )

        logger.info(
            "Tool execution completed: tool=%s status=%s",
            tool_name,
            "error" if "error" in result else "success",
        )

        return result

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
