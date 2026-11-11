"""Validate returned maintenance evidence against the requested identifiers."""


def validate_evidence_result(
    tool_name: str,
    tool_input: dict,
    result: dict,
) -> dict:
    """Check that an evidence result belongs to the requested record."""

    if not isinstance(tool_input, dict):
        return {
            "valid": False,
            "reason": "tool input must be a dictionary",
        }

    if not isinstance(result, dict):
        return {
            "valid": False,
            "reason": "tool result must be a dictionary",
        }

    if "error" in result:
        return {
            "valid": False,
            "reason": "tool returned an error",
        }

    if tool_name == "get_equipment_alert":
        identifier_field = "alert_id"
    elif tool_name in {
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }:
        identifier_field = "asset_id"
    else:
        return {
            "valid": False,
            "reason": "unsupported evidence tool",
        }

    expected_identifier = tool_input.get(identifier_field)

    if (
        not isinstance(expected_identifier, str)
        or not expected_identifier.strip()
    ):
        return {
            "valid": False,
            "reason": "invalid requested identifier",
        }

    if result.get(identifier_field) != expected_identifier:
        return {
            "valid": False,
            "reason": "evidence result identifier mismatch",
        }

    return {"valid": True}
