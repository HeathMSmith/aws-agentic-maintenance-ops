from datetime import timedelta, timezone

import pytest

from simulation.clock import parse_simulation_time


def test_parse_utc_timestamp():
    result = parse_simulation_time("2026-11-09T14:30:00Z")

    assert result.isoformat() == "2026-11-09T14:30:00+00:00"
    assert result.utcoffset() == timedelta(0)


def test_parse_timestamp_with_offset():
    result = parse_simulation_time("2026-11-09T09:30:00-05:00")

    assert result.utcoffset() == timedelta(hours=-5)
    assert result.astimezone(timezone.utc).isoformat() == (
        "2026-11-09T14:30:00+00:00"
    )


def test_calculate_time_until_maintenance():
    incident_time = parse_simulation_time("2026-11-09T14:30:00Z")
    maintenance_start = parse_simulation_time("2026-11-09T22:00:00Z")

    hours_until = (
        maintenance_start - incident_time
    ).total_seconds() / 3600

    assert hours_until == 7.5


@pytest.mark.parametrize("timestamp", ["", "   ", None, 123])
def test_reject_invalid_input(timestamp):
    with pytest.raises(ValueError, match="timestamp must be a non-empty string"):
        parse_simulation_time(timestamp)


def test_reject_invalid_datetime():
    with pytest.raises(ValueError, match="timestamp must be a valid ISO 8601 datetime"):
        parse_simulation_time("not-a-timestamp")


def test_reject_timestamp_without_timezone():
    with pytest.raises(ValueError, match="timestamp must include timezone information"):
        parse_simulation_time("2026-11-09T14:30:00")
