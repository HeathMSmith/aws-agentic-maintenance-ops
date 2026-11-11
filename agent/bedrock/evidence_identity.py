"""Validate evidence-tool request identifiers against authoritative alert data."""

from agent.tools.equipment_alert import get_equipment_alert


ASSET_EVIDENCE_TOOLS = frozenset(
    {
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }
)


def validate_evidence_identity(
    execution_trace: list,
    alert_id: str,
) -> dict:
    """Confirm required evidence tools queried the requested alert and asset."""

    if not isinstance(alert_id, str) or not alert_id.strip():
        return {
            "valid": False,
            "reason": "alert_id must be a non-empty string",
        }

    if not isinstance(execution_trace, list):
        return {
            "valid": False,
            "reason": "execution trace must be a list",
        }

    alert = get_equipment_alert(alert_id)

    if "error" in alert:
        return {
            "valid": False,
            "reason": "requested alert was not found",
        }

    expected_asset_id = alert.get("asset_id")

    if not isinstance(expected_asset_id, str) or not expected_asset_id.strip():
        return {
            "valid": False,
            "reason": "requested alert has no valid asset_id",
        }

    required_identifiers = {
        "get_equipment_alert": ("alert_id", alert_id),
        **{
            tool_name: ("asset_id", expected_asset_id)
            for tool_name in ASSET_EVIDENCE_TOOLS
        },
    }

    matched_tools = set()

    for entry in execution_trace:
        if not isinstance(entry, dict):
            continue

        tool_name = entry.get("tool_name")

        if tool_name not in required_identifiers:
            continue

        if entry.get("status") != "success":
            continue

        identifiers = entry.get("identifiers")

        if not isinstance(identifiers, dict):
            continue

        identifier_field, expected_value = required_identifiers[tool_name]

        if identifiers.get(identifier_field) == expected_value:
            matched_tools.add(tool_name)

    missing_or_mismatched = sorted(
        set(required_identifiers) - matched_tools
    )

    if missing_or_mismatched:
        return {
            "valid": False,
            "reason": "required evidence tool identifiers did not match",
            "missing_or_mismatched_tools": missing_or_mismatched,
        }

    return {
        "valid": True,
        "alert_id": alert_id,
        "asset_id": expected_asset_id,
    }
