from simulation.schedule_analysis import get_next_maintenance_window


def validate_maintenance_window(
    investigation: dict,
) -> dict:
    """Verify maintenance-window analysis against source schedule data."""

    try:
        alert = investigation["alert"]
        production_schedule = investigation["production_schedule"]
        reported_window = investigation["maintenance_window"]

        expected_window = get_next_maintenance_window(
            production_schedule["schedule"],
            alert["timestamp"],
        )

    except (KeyError, TypeError, ValueError) as exc:
        return {
            "valid": False,
            "reason": f"invalid maintenance window evidence: {exc}",
        }

    if reported_window != expected_window:
        return {
            "valid": False,
            "reason": "maintenance window does not match production schedule",
        }

    return {"valid": True}
