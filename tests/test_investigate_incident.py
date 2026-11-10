from unittest.mock import patch

from simulation.investigate_incident import investigate_incident


def test_investigate_existing_incident():
    result = investigate_incident("ALERT-0001")

    assert result["status"] == "investigated"
    assert result["alert_id"] == "ALERT-0001"
    assert result["alert"]["asset_id"] == "CONV-MTR-042"
    assert result["asset"]["asset_id"] == "CONV-MTR-042"
    assert result["asset"]["criticality"] == "high"
    assert result["maintenance_history"]["asset_id"] == "CONV-MTR-042"
    assert result["maintenance_history"]["record_count"] == 2
    assert result["maintenance_history"]["records"][0]["record_id"] == "MAINT-0002"
    assert result["production_schedule"]["asset_id"] == "CONV-MTR-042"
    assert result["production_schedule"]["line_id"] == "PKG-LINE-02"
    assert result["production_schedule"]["line_status"] == "active"
    assert len(result["production_schedule"]["schedule"]) == 2
    assert result["maintenance_window"]["available"] is True
    assert result["maintenance_window"]["schedule_id"] == "MAINT-WINDOW-0001"
    assert result["maintenance_window"]["hours_until_start"] == 7.5
    assert result["maintenance_window"]["remaining_duration_hours"] == 4.0


def test_investigate_nonexistent_alert():
    result = investigate_incident("INVALID-ALERT")

    assert result == {
        "status": "failed",
        "error": "Alert not found: INVALID-ALERT",
    }


def test_investigate_missing_asset():
    simulated_alert = {
        "alert_id": "ALERT-MISSING-ASSET",
        "asset_id": "UNKNOWN-MOTOR",
    }

    with patch(
        "simulation.investigate_incident.get_equipment_alert",
        return_value=simulated_alert,
    ):
        result = investigate_incident("ALERT-MISSING-ASSET")

    assert result == {
        "status": "failed",
        "alert_id": "ALERT-MISSING-ASSET",
        "error": "Asset not found: UNKNOWN-MOTOR",
    }


def test_investigate_asset_without_maintenance_history():
    empty_history = {
        "asset_id": "CONV-MTR-042",
        "record_count": 0,
        "records": [],
    }

    with patch(
        "simulation.investigate_incident.get_maintenance_history",
        return_value=empty_history,
    ):
        result = investigate_incident("ALERT-0001")

    assert result["status"] == "investigated"
    assert result["maintenance_history"] == empty_history


def test_investigate_maintenance_history_lookup_failure():
    with patch(
        "simulation.investigate_incident.get_maintenance_history",
        return_value={"error": "Maintenance history unavailable"},
    ):
        result = investigate_incident("ALERT-0001")

    assert result == {
        "status": "failed",
        "alert_id": "ALERT-0001",
        "error": "Maintenance history unavailable",
    }

def test_investigate_production_schedule_lookup_failure():
    with patch(
        "simulation.investigate_incident.get_production_schedule",
        return_value={"error": "Production schedule unavailable"},
    ):
        result = investigate_incident("ALERT-0001")

    assert result == {
        "status": "failed",
        "alert_id": "ALERT-0001",
        "error": "Production schedule unavailable",
    }

def test_investigate_invalid_maintenance_window():
    with patch(
        "simulation.investigate_incident.get_next_maintenance_window",
        side_effect=ValueError("maintenance window end must be after start"),
    ):
        result = investigate_incident("ALERT-0001")

    assert result == {
        "status": "failed",
        "alert_id": "ALERT-0001",
        "error": (
            "Invalid maintenance schedule data: "
            "maintenance window end must be after start"
        ),
    }
    