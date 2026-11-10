from datetime import datetime


def parse_simulation_time(timestamp: str) -> datetime:
    """Parse an ISO 8601 timestamp with an explicit UTC offset."""
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("timestamp must be a non-empty string")

    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO 8601 datetime") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")

    return parsed
