import pytest

from simulation.schedule_analysis import get_next_maintenance_window


INCIDENT_TIME = "2026-11-09T14:30:00Z"


def make_window(schedule_id, start, end):
    return {
        "schedule_id": schedule_id,
        "activity": "planned_maintenance_window",
        "start": start,
        "end": end,
    }


def test_future_maintenance_window():
    schedule = [
        make_window(
            "WINDOW-001",
            "2026-11-09T22:00:00Z",
            "2026-11-10T02:00:00Z",
        )
    ]

    result = get_next_maintenance_window(schedule, INCIDENT_TIME)

    assert result["available"] is True
    assert result["schedule_id"] == "WINDOW-001"
    assert result["hours_until_start"] == 7.5
    assert result["remaining_duration_hours"] == 4.0


def test_active_maintenance_window():
    schedule = [
        make_window(
            "WINDOW-001",
            "2026-11-09T13:00:00Z",
            "2026-11-09T17:00:00Z",
        )
    ]

    result = get_next_maintenance_window(schedule, INCIDENT_TIME)

    assert result["available"] is True
    assert result["hours_until_start"] == 0.0
    assert result["remaining_duration_hours"] == 2.5


def test_expired_maintenance_window():
    schedule = [
        make_window(
            "WINDOW-001",
            "2026-11-09T08:00:00Z",
            "2026-11-09T12:00:00Z",
        )
    ]

    result = get_next_maintenance_window(schedule, INCIDENT_TIME)

    assert result == {
        "available": False,
        "reason": "No upcoming maintenance window found",
    }


def test_no_maintenance_windows():
    result = get_next_maintenance_window([], INCIDENT_TIME)

    assert result["available"] is False


def test_ignores_production_entries():
    schedule = [
        {
            "schedule_id": "PROD-001",
            "activity": "scheduled_production",
            "start": "2026-11-09T06:00:00Z",
            "end": "2026-11-09T22:00:00Z",
        }
    ]

    result = get_next_maintenance_window(schedule, INCIDENT_TIME)

    assert result["available"] is False


def test_selects_earliest_available_window():
    schedule = [
        make_window(
            "WINDOW-LATER",
            "2026-11-11T22:00:00Z",
            "2026-11-12T02:00:00Z",
        ),
        make_window(
            "WINDOW-SOONER",
            "2026-11-09T22:00:00Z",
            "2026-11-10T02:00:00Z",
        ),
    ]

    result = get_next_maintenance_window(schedule, INCIDENT_TIME)

    assert result["schedule_id"] == "WINDOW-SOONER"
    assert result["hours_until_start"] == 7.5


def test_rejects_invalid_window_duration():
    schedule = [
        make_window(
            "WINDOW-INVALID",
            "2026-11-09T22:00:00Z",
            "2026-11-09T20:00:00Z",
        )
    ]

    with pytest.raises(
        ValueError,
        match="maintenance window end must be after start",
    ):
        get_next_maintenance_window(schedule, INCIDENT_TIME)
