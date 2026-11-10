from simulation.clock import parse_simulation_time


def get_next_maintenance_window(schedule: list, incident_timestamp: str) -> dict:
    """Find the next available maintenance window relative to an incident."""

    incident_time = parse_simulation_time(incident_timestamp)
    maintenance_windows = []

    for entry in schedule:
        if entry["activity"] != "planned_maintenance_window":
            continue

        start = parse_simulation_time(entry["start"])
        end = parse_simulation_time(entry["end"])

        if end <= start:
            raise ValueError("maintenance window end must be after start")

        if end <= incident_time:
            continue

        maintenance_windows.append((start, end, entry))

    if not maintenance_windows:
        return {
            "available": False,
            "reason": "No upcoming maintenance window found",
        }

    start, end, entry = min(
        maintenance_windows,
        key=lambda window: max(window[0], incident_time),
    )

    effective_start = max(start, incident_time)

    return {
        "available": True,
        "schedule_id": entry["schedule_id"],
        "start": entry["start"],
        "end": entry["end"],
        "hours_until_start": round(
            (effective_start - incident_time).total_seconds() / 3600, 2
        ),
        "remaining_duration_hours": round(
            (end - effective_start).total_seconds() / 3600, 2
        ),
    }
