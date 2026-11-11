"""Validate returned maintenance evidence against the requested identifiers."""
from simulation.clock import parse_simulation_time

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
    if tool_name == "get_maintenance_history":
        records = result.get("records")
        record_count = result.get("record_count")

        if (
            not isinstance(records, list)
            or not isinstance(record_count, int)
            or isinstance(record_count, bool)
            or record_count < 0
            or record_count != len(records)
        ):
            return {
                "valid": False,
                "reason": "invalid maintenance history structure",
            }

        for record in records:
            if (
                not isinstance(record, dict)
                or record.get("asset_id") != expected_identifier
            ):
                return {
                    "valid": False,
                    "reason": "invalid maintenance history structure",
            }
    if tool_name == "get_production_schedule":
        schedule = result.get("schedule")

        if not isinstance(schedule, list):
            return {
                "valid": False,
                "reason": "invalid production schedule structure",
            }

        for entry in schedule:
            if not isinstance(entry, dict):
                return {
                    "valid": False,
                    "reason": "invalid production schedule structure",
                }

            try:
                start = parse_simulation_time(entry["start"])
                end = parse_simulation_time(entry["end"])
            except (KeyError, TypeError, ValueError):
                return {
                    "valid": False,
                    "reason": "invalid production schedule structure",
                }

            if start >= end:
                return {
                    "valid": False,
                    "reason": "invalid production schedule structure",
                }
    if tool_name == "get_maintenance_window_status":
        maintenance_window = result.get("maintenance_window")

        if (
            not isinstance(maintenance_window, dict)
            or not isinstance(maintenance_window.get("available"), bool)
        ):
            return {
                "valid": False,
                "reason": "invalid maintenance window structure",
            }
    return {"valid": True}
