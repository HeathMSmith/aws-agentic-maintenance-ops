import pytest

from agent.tools.equipment_alert import get_equipment_alert


def test_get_existing_alert():
    result = get_equipment_alert("ALERT-0001")

    assert result["alert_id"] == "ALERT-0001"
    assert result["asset_id"] == "CONV-MTR-042"
    assert result["severity"] == "warning"
    assert result["status"] == "new"
    assert result["observations"]["vibration_rms_mm_s"] == 8.2
    assert result["observations"]["temperature_c"] == 89.0


def test_get_nonexistent_alert():
    result = get_equipment_alert("INVALID-ALERT")

    assert result == {"error": "Alert not found: INVALID-ALERT"}


@pytest.mark.parametrize("alert_id", ["", "   ", None, 123])
def test_get_alert_invalid_input(alert_id):
    result = get_equipment_alert(alert_id)

    assert result == {"error": "alert_id must be a non-empty string"}
