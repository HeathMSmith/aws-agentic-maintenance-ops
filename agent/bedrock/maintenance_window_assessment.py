
"""Build deterministic maintenance-window assessments."""


def build_maintenance_window_assessment(operational_facts: dict) -> dict:
    """Summarize validated maintenance-window availability."""

    available = operational_facts["maintenance_window_available"]
    reference_timestamp = operational_facts["reference_timestamp"]

    if available is False:
        summary = (
            "No active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        )
    else:
        summary = (
            "An active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        )

    return {
        "available": available,
        "reference_timestamp": reference_timestamp,
        "summary": summary,
    }
