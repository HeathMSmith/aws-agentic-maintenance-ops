from simulation.clock import parse_simulation_time


ALLOWED_ACTIVITIES = {
    "scheduled_production",
    "planned_maintenance_window",
}


def validate_schedule_integrity(schedule: list) -> dict:
    """Validate activity intervals within a single production-line schedule."""

    if not isinstance(schedule, list):
        return {
            "valid": False,
            "reason": "production schedule must be a list",
        }

    intervals = []
    schedule_ids = set()

    for entry in schedule:
        if not isinstance(entry, dict):
            return {
                "valid": False,
                "reason": "invalid production schedule entry",
            }

        schedule_id = entry.get("schedule_id")

        if not isinstance(schedule_id, str) or not schedule_id.strip():
            return {
                "valid": False,
                "reason": "invalid production schedule ID",
            }

        if schedule_id in schedule_ids:
            return {
                "valid": False,
                "reason": "duplicate production schedule ID",
            }

        schedule_ids.add(schedule_id)

        if entry.get("activity") not in ALLOWED_ACTIVITIES:
            return {
                "valid": False,
                "reason": "unsupported production schedule activity",
            }

        try:
            start = parse_simulation_time(entry["start"])
            end = parse_simulation_time(entry["end"])
        except (KeyError, TypeError, ValueError):
            return {
                "valid": False,
                "reason": "invalid production schedule timestamp",
            }

        if end <= start:
            return {
                "valid": False,
                "reason": "production schedule end must be after start",
            }

        intervals.append((start, end))

    intervals.sort(key=lambda interval: interval[0])

    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            return {
                "valid": False,
                "reason": "overlapping production schedule activities",
            }

    return {"valid": True}
