from copy import deepcopy

import pytest

from agent.tools.production_schedule import get_production_schedule
from simulation.policies.schedule_integrity import validate_schedule_integrity


@pytest.fixture
def schedule():
    """Provide a fresh production-line schedule for each test."""
    schedule_data = get_production_schedule("CONV-MTR-042")
    return deepcopy(schedule_data["schedule"])


def test_valid_production_schedule(schedule):
    assert validate_schedule_integrity(schedule) == {"valid": True}


def test_adjacent_activities_are_valid(schedule):
    """Activities sharing a boundary timestamp do not overlap."""
    assert schedule[0]["end"] == schedule[1]["start"]
    assert validate_schedule_integrity(schedule) == {"valid": True}


def test_reject_overlapping_activities(schedule):
    schedule[1]["start"] = "2026-11-09T21:00:00Z"

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "overlapping production schedule activities",
    }


def test_reject_invalid_duration(schedule):
    schedule[1]["end"] = schedule[1]["start"]

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "production schedule end must be after start",
    }


def test_reject_duplicate_schedule_id(schedule):
    schedule[1]["schedule_id"] = schedule[0]["schedule_id"]

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "duplicate production schedule ID",
    }


def test_reject_unsupported_activity(schedule):
    schedule[1]["activity"] = "unknown_activity"

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "unsupported production schedule activity",
    }


@pytest.mark.parametrize(
    "timestamp",
    [
        "invalid-timestamp",
        None,
        "2026-11-09T22:00:00",
    ],
)
def test_reject_invalid_timestamp(schedule, timestamp):
    schedule[1]["start"] = timestamp

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "invalid production schedule timestamp",
    }


def test_reject_duplicate_or_missing_schedule_structure():
    assert validate_schedule_integrity(None) == {
        "valid": False,
        "reason": "production schedule must be a list",
    }


def test_reject_invalid_schedule_entry(schedule):
    schedule.append(None)

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "invalid production schedule entry",
    }


def test_reject_missing_schedule_id(schedule):
    schedule[1].pop("schedule_id")

    assert validate_schedule_integrity(schedule) == {
        "valid": False,
        "reason": "invalid production schedule ID",
    }
