import pytest

from agent.tools.production_schedule import get_production_schedule


def test_get_existing_production_schedule():
    result = get_production_schedule("CONV-MTR-042")

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["line_id"] == "PKG-LINE-02"
    assert result["line_name"] == "Packaging Line 2"
    assert result["line_status"] == "active"
    assert len(result["schedule"]) == 2


def test_production_schedule_chronological_order():
    result = get_production_schedule("CONV-MTR-042")

    assert result["schedule"][0]["schedule_id"] == "PROD-0001"
    assert result["schedule"][1]["schedule_id"] == "MAINT-WINDOW-0001"

    start_times = [entry["start"] for entry in result["schedule"]]
    assert start_times == sorted(start_times)


def test_get_nonexistent_production_schedule():
    result = get_production_schedule("UNKNOWN-ASSET")

    assert result == {
        "error": "No production schedule found for asset: UNKNOWN-ASSET"
    }


@pytest.mark.parametrize("asset_id", ["", "   ", None, 123])
def test_get_production_schedule_invalid_input(asset_id):
    result = get_production_schedule(asset_id)

    assert result == {"error": "asset_id must be a non-empty string"}
