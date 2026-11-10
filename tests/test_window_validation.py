from copy import deepcopy

import pytest

from simulation.investigate_incident import investigate_incident
from simulation.policies.window_validation import validate_maintenance_window


@pytest.fixture
def investigation():
    """Provide an isolated investigation context for each test."""
    return deepcopy(investigate_incident("ALERT-0001"))


def test_valid_maintenance_window(investigation):
    result = validate_maintenance_window(investigation)

    assert result == {"valid": True}


@pytest.mark.parametrize(
    "field,value",
    [
        ("hours_until_start", 1.0),
        ("remaining_duration_hours", 2.0),
        ("schedule_id", "WRONG-WINDOW"),
        ("start", "2026-11-09T20:00:00Z"),
        ("end", "2026-11-10T04:00:00Z"),
    ],
)
def test_reject_inconsistent_window_fields(investigation, field, value):
    investigation["maintenance_window"][field] = value

    result = validate_maintenance_window(investigation)

    assert result == {
        "valid": False,
        "reason": "maintenance window does not match production schedule",
    }


@pytest.mark.parametrize(
    "field",
    [
        "alert",
        "production_schedule",
        "maintenance_window",
    ],
)
def test_reject_missing_evidence(investigation, field):
    investigation.pop(field)

    result = validate_maintenance_window(investigation)

    assert result["valid"] is False
    assert result["reason"].startswith("invalid maintenance window evidence:")


def test_reject_missing_schedule_entries(investigation):
    investigation["production_schedule"].pop("schedule")

    result = validate_maintenance_window(investigation)

    assert result["valid"] is False
    assert result["reason"].startswith("invalid maintenance window evidence:")


def test_reject_invalid_incident_timestamp(investigation):
    investigation["alert"]["timestamp"] = "invalid-timestamp"

    result = validate_maintenance_window(investigation)

    assert result["valid"] is False
    assert result["reason"].startswith("invalid maintenance window evidence:")


def test_reject_invalid_window_duration(investigation):
    investigation["production_schedule"]["schedule"][1]["end"] = (
        "2026-11-09T20:00:00Z"
    )

    result = validate_maintenance_window(investigation)

    assert result["valid"] is False
    assert result["reason"].startswith("invalid maintenance window evidence:")
