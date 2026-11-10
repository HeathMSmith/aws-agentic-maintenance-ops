from unittest.mock import patch

from simulation.investigate_incident import investigate_incident


def test_investigate_existing_incident():
    result = investigate_incident("ALERT-0001")

    assert result["status"] == "investigated"
    assert result["alert_id"] == "ALERT-0001"
    assert result["alert"]["asset_id"] == "CONV-MTR-042"
    assert result["asset"]["asset_id"] == "CONV-MTR-042"
    assert result["asset"]["criticality"] == "high"


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
