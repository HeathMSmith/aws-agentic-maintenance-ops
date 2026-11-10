from agent.tools.asset_context import get_asset_context
from agent.tools.equipment_alert import get_equipment_alert
from agent.tools.maintenance_history import get_maintenance_history


def investigate_incident(alert_id: str) -> dict:
    """Gather alert evidence and associated operational context."""

    alert = get_equipment_alert(alert_id)

    if "error" in alert:
        return {
            "status": "failed",
            "error": alert["error"],
        }

    asset = get_asset_context(alert["asset_id"])

    if "error" in asset:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": asset["error"],
        }

    maintenance_history = get_maintenance_history(alert["asset_id"])

    if "error" in maintenance_history:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": maintenance_history["error"],
        }

    return {
        "status": "investigated",
        "alert_id": alert_id,
        "alert": alert,
        "asset": asset,
        "maintenance_history": maintenance_history,
    }
