from simulation.policies.window_validation import validate_maintenance_window

def validate_investigation_evidence(investigation: dict) -> dict:
    """Validate required evidence and asset relationships."""

    if not isinstance(investigation, dict):
        return {
            "valid": False,
            "reason": "investigation must be a dictionary",
        }

    if investigation.get("status") != "investigated":
        return {
            "valid": False,
            "reason": "investigation is incomplete",
        }

    required_fields = [
        "alert",
        "asset",
        "maintenance_history",
        "production_schedule",
        "maintenance_window",
    ]

    for field in required_fields:
        if not isinstance(investigation.get(field), dict):
            return {
                "valid": False,
                "reason": f"missing or invalid evidence: {field}",
            }

    alert = investigation["alert"]
    asset = investigation["asset"]
    history = investigation["maintenance_history"]
    schedule = investigation["production_schedule"]

    asset_id = alert.get("asset_id")

    if not isinstance(asset_id, str) or not asset_id.strip():
        return {
            "valid": False,
            "reason": "missing or invalid alert asset_id",
        }

    for source_name, source in [
        ("asset", asset),
        ("maintenance_history", history),
        ("production_schedule", schedule),
    ]:
        if source.get("asset_id") != asset_id:
            return {
                "valid": False,
                "reason": f"asset_id mismatch: {source_name}",
            }

    records = history.get("records")

    if not isinstance(records, list):
        return {
            "valid": False,
            "reason": "invalid maintenance history records",
        }

    if any(
        not isinstance(record, dict)
        or record.get("asset_id") != asset_id
        for record in records
    ):
        return {
            "valid": False,
            "reason": "maintenance history contains mismatched asset records",
        }

    window_validation = validate_maintenance_window(investigation)

    if not window_validation["valid"]:
        return window_validation

    return {"valid": True}
