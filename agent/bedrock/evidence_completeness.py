"""Validate required evidence-tool execution during Bedrock investigations."""


REQUIRED_EVIDENCE_TOOLS = frozenset(
    {
        "get_equipment_alert",
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }
)


def validate_evidence_completeness(execution_trace: list) -> dict:
    """Check that all required evidence tools completed successfully."""

    if not isinstance(execution_trace, list):
        return {
            "valid": False,
            "reason": "execution trace must be a list",
        }

    successful_tools = {
        entry["tool_name"]
        for entry in execution_trace
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("tool_name"), str)
            and entry.get("status") == "success"
        )
    }

    missing_tools = sorted(REQUIRED_EVIDENCE_TOOLS - successful_tools)

    if missing_tools:
        return {
            "valid": False,
            "reason": "required evidence tools were not completed",
            "missing_tools": missing_tools,
        }

    return {
        "valid": True,
        "completed_tools": sorted(REQUIRED_EVIDENCE_TOOLS),
    }
