import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "maintenance_history.json"


def get_maintenance_history(asset_id: str) -> dict:
    """Retrieve maintenance records associated with an asset."""
    if not isinstance(asset_id, str) or not asset_id.strip():
        return {"error": "asset_id must be a non-empty string"}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    records = [
        record
        for record in data["maintenance_records"]
        if record["asset_id"] == asset_id
    ]

    records.sort(key=lambda record: record["date"], reverse=True)

    return {
        "asset_id": asset_id,
        "record_count": len(records),
        "records": records,
    }
