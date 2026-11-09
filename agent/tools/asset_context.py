import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "assets.json"


def get_asset_context(asset_id: str) -> dict:
    """Retrieve asset metadata by asset ID."""
    if not isinstance(asset_id, str) or not asset_id.strip():
        return {"error": "asset_id must be a non-empty string"}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for asset in data["assets"]:
        if asset["asset_id"] == asset_id:
            return asset

    return {"error": f"Asset not found: {asset_id}"}
