"""Retrieve deterministic maintenance-window availability for an asset."""

from agent.tools.production_schedule import get_production_schedule
from simulation.schedule_analysis import get_maintenance_window_at


def get_maintenance_window_status(
    asset_id: str,
    reference_timestamp: str,
) -> dict:
    """Evaluate maintenance availability relative to an explicit timestamp."""

    if not isinstance(asset_id, str) or not asset_id.strip():
        return {
            "error": "asset_id must be a non-empty string",
        }

    schedule_result = get_production_schedule(asset_id)

    if "error" in schedule_result:
        return schedule_result

    try:
        window_result = get_maintenance_window_at(
            schedule_result["schedule"],
            reference_timestamp,
        )
    except ValueError as exc:
        return {
            "error": "invalid_reference_timestamp",
            "message": str(exc),
        }

    return {
        "asset_id": asset_id,
        "line_id": schedule_result["line_id"],
        "reference_timestamp": reference_timestamp,
        "maintenance_window": window_result,
    }
