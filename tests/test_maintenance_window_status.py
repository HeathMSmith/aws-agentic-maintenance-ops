import pytest

from agent.tools.maintenance_window_status import get_maintenance_window_status


def test_window_available_at_incident_time():
    result = get_maintenance_window_status(
        "CONV-MTR-042",
        "2026-11-09T14:30:00Z",
    )

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["line_id"] == "PKG-LINE-02"
    assert result["reference_timestamp"] == "2026-11-09T14:30:00Z"

    window = result["maintenance_window"]

    assert window["available"] is True
    assert window["schedule_id"] == "MAINT-WINDOW-0001"
    assert window["hours_until_start"] == 7.5
    assert window["remaining_duration_hours"] == 4.0


def test_window_expired_at_later_reference_time():
    result = get_maintenance_window_status(
        "CONV-MTR-042",
        "2026-11-10T18:00:00Z",
    )

    assert result["reference_timestamp"] == "2026-11-10T18:00:00Z"
    assert result["maintenance_window"] == {
        "available": False,
        "reason": "No upcoming maintenance window found",
    }


def test_missing_production_schedule():
    result = get_maintenance_window_status(
        "UNKNOWN-ASSET",
        "2026-11-10T18:00:00Z",
    )

    assert result == {
        "error": "No production schedule found for asset: UNKNOWN-ASSET",
    }


@pytest.mark.parametrize(
    "asset_id",
    ["", "   ", None, 123],
)
def test_invalid_asset_id(asset_id):
    result = get_maintenance_window_status(
        asset_id,
        "2026-11-10T18:00:00Z",
    )

    assert result == {
        "error": "asset_id must be a non-empty string",
    }


@pytest.mark.parametrize(
    "timestamp",
    ["", "invalid-timestamp", "2026-11-10T18:00:00", None, 123],
)
def test_invalid_reference_timestamp(timestamp):
    result = get_maintenance_window_status(
        "CONV-MTR-042",
        timestamp,
    )

    assert result["error"] == "invalid_reference_timestamp"
    assert isinstance(result["message"], str)
