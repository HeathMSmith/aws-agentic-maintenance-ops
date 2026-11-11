from datetime import datetime, timezone

import pytest

from agent.bedrock.execution_context import create_execution_context
from simulation.clock import parse_simulation_time


def test_historical_timestamp_normalized_to_utc():
    result = create_execution_context(
        "2026-11-10T13:00:00-05:00"
    )

    assert result == {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }


def test_utc_timestamp_preserved():
    result = create_execution_context(
        "2026-11-10T18:00:00Z"
    )

    assert result == {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }


def test_current_execution_context_uses_utc():
    before = datetime.now(timezone.utc)

    result = create_execution_context()

    after = datetime.now(timezone.utc)

    timestamp = parse_simulation_time(
        result["reference_timestamp"]
    )

    assert result["reference_timestamp"].endswith("Z")
    assert timestamp.tzinfo is not None
    assert before <= timestamp <= after


@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "   ",
        "invalid-timestamp",
        "2026-11-10T18:00:00",
        123,
    ],
)
def test_invalid_reference_timestamp_rejected(timestamp):
    with pytest.raises(ValueError):
        create_execution_context(timestamp)
