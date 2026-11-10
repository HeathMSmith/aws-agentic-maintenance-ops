import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "equipment_alerts.json"


def get_equipment_alert(alert_id: str) -> dict:
    """Retrieve an equipment alert by alert ID."""
    if not isinstance(alert_id, str) or not alert_id.strip():
        return {"error": "alert_id must be a non-empty string"}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for alert in data["alerts"]:
        if alert["alert_id"] == alert_id:
            return alert

    return {"error": f"Alert not found: {alert_id}"}
