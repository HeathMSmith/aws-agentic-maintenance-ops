
"""Validate returned maintenance evidence against the requested identifiers."""

import math

from simulation.clock import parse_simulation_time


def _validate_equipment_alert(result: dict) -> dict:
    """Validate equipment-alert fields and measurement consistency."""

    required_strings = (
        "asset_id",
        "alert_type",
        "severity",
        "status",
    )

    for field in required_strings:
        value = result.get(field)

        if not isinstance(value, str) or not value.strip():
            return {
                "valid": False,
                "reason": "invalid equipment alert structure",
            }

    try:
        parse_simulation_time(result["timestamp"])
    except (KeyError, TypeError, ValueError):
        return {
            "valid": False,
            "reason": "invalid equipment alert structure",
        }

    for field in ("observations", "baseline"):
        value = result.get(field)

        if not isinstance(value, dict) or not value:
            return {
                "valid": False,
                "reason": "invalid equipment alert structure",
            }

    for field in ("observations", "baseline"):
        measurements = result[field]

        for measurement_value in measurements.values():
            if (
                not isinstance(measurement_value, (int, float))
                or isinstance(measurement_value, bool)
                or not math.isfinite(measurement_value)
            ):
                return {
                    "valid": False,
                    "reason": "invalid equipment alert measurements",
                }

    observations = result["observations"]
    baseline = result["baseline"]

    if set(observations) != set(baseline):
        return {
            "valid": False,
            "reason": "equipment alert measurement keys mismatch",
        }

    return {"valid": True}

def _validate_asset_context(result: dict) -> dict:
    """Validate asset metadata and maintenance properties."""

    required_strings = (
        "name",
        "asset_type",
        "location",
        "criticality",
        "operational_status",
        "manufacturer",
    )

    for field in required_strings:
        value = result.get(field)

        if not isinstance(value, str) or not value.strip():
            return {
                "valid": False,
                "reason": "invalid asset context structure",
            }

    if result["criticality"] not in {"low", "medium", "high"}:
        return {
            "valid": False,
            "reason": "invalid asset criticality",
        }

    rated_power = result.get("rated_power_kw")

    if (
        not isinstance(rated_power, (int, float))
        or isinstance(rated_power, bool)
        or not math.isfinite(rated_power)
        or rated_power < 0
    ):
        return {
            "valid": False,
            "reason": "invalid asset rated power",
        }

    maintenance_interval = result.get("maintenance_interval_days")

    if (
        not isinstance(maintenance_interval, int)
        or isinstance(maintenance_interval, bool)
        or maintenance_interval <= 0
    ):
        return {
            "valid": False,
            "reason": "invalid asset maintenance interval",
        }

    return {"valid": True}

def _validate_maintenance_history(
    result: dict,
    expected_identifier: str,
) -> dict:
    """Validate maintenance records against the requested asset."""

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

    return {"valid": True}

def _validate_production_schedule(result: dict) -> dict:
    """Validate production-schedule entries and time ranges."""

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

    return {"valid": True}

def _validate_maintenance_window(result: dict) -> dict:
    """Validate maintenance-window availability information."""

    maintenance_window = result.get("maintenance_window")

    if not isinstance(maintenance_window, dict) or not isinstance(
        maintenance_window.get("available"), bool
    ):
        return {
            "valid": False,
            "reason": "invalid maintenance window structure",
        }

    return {"valid": True}

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

    if not isinstance(expected_identifier, str) or not expected_identifier.strip():
        return {
            "valid": False,
            "reason": "invalid requested identifier",
        }

    if result.get(identifier_field) != expected_identifier:
        return {
            "valid": False,
            "reason": "evidence result identifier mismatch",
        }

    if tool_name == "get_equipment_alert":
        return _validate_equipment_alert(result)

    if tool_name == "get_asset_context":
        return _validate_asset_context(result)

    if tool_name == "get_maintenance_history":
        return _validate_maintenance_history(
            result,
            expected_identifier,
        )

    if tool_name == "get_production_schedule":
        return _validate_production_schedule(result)

    if tool_name == "get_maintenance_window_status":
        return _validate_maintenance_window(result)
