from agent.tools.asset_context import get_asset_context
from agent.tools.equipment_alert import get_equipment_alert
from agent.tools.maintenance_history import get_maintenance_history
from agent.tools.production_schedule import get_production_schedule
from simulation.schedule_analysis import get_next_maintenance_window


def investigate_incident(alert_id: str) -> dict:
    """Gather alert evidence and associated operational context."""

    alert = get_equipment_alert(alert_id)

    if "error" in alert:
        return {
            "status": "failed",
            "error": alert["error"],
        }

    asset_id = alert["asset_id"]
    asset = get_asset_context(asset_id)

    if "error" in asset:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": asset["error"],
        }

    maintenance_history = get_maintenance_history(asset_id)

    if "error" in maintenance_history:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": maintenance_history["error"],
        }

    production_schedule = get_production_schedule(asset_id)

    if "error" in production_schedule:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": production_schedule["error"],
        }
    try:
        maintenance_window = get_next_maintenance_window(
            production_schedule["schedule"],
            alert["timestamp"],
        )
    except (ValueError, KeyError, TypeError) as exc:
        return {
            "status": "failed",
            "alert_id": alert_id,
            "error": f"Invalid maintenance schedule data: {exc}",
        }

    return {
        "status": "investigated",
        "alert_id": alert_id,
        "alert": alert,
        "asset": asset,
        "maintenance_history": maintenance_history,
        "production_schedule": production_schedule,
        "maintenance_window": maintenance_window,
    }
