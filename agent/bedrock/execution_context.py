"""Create trusted execution context for Bedrock investigations."""

from datetime import datetime, timezone

from simulation.clock import parse_simulation_time


def create_execution_context(
    reference_timestamp: str | None = None,
) -> dict:
    """Create a validated reference timestamp for an investigation."""

    if reference_timestamp is None:
        reference_timestamp = datetime.now(timezone.utc).isoformat()

    parsed = parse_simulation_time(reference_timestamp)

    return {
        "reference_timestamp": parsed.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }
