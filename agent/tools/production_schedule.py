import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "production_schedule.json"


def get_production_schedule(asset_id: str) -> dict:
    """Retrieve the production schedule associated with an asset."""
    if not isinstance(asset_id, str) or not asset_id.strip():
        return {"error": "asset_id must be a non-empty string"}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for line in data["production_lines"]:
        if asset_id in line["assets"]:
            return {
                "asset_id": asset_id,
                "line_id": line["line_id"],
                "line_name": line["name"],
                "line_status": line["status"],
                "schedule": sorted(
                    line["schedule"],
                    key=lambda entry: entry["start"],
                ),
            }

    return {"error": f"No production schedule found for asset: {asset_id}"}
