import pytest

from agent.tools.maintenance_history import get_maintenance_history


def test_get_existing_maintenance_history():
    result = get_maintenance_history("CONV-MTR-042")

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["record_count"] == 2
    assert len(result["records"]) == 2


def test_maintenance_history_newest_first():
    result = get_maintenance_history("CONV-MTR-042")

    assert result["records"][0]["record_id"] == "MAINT-0002"
    assert result["records"][1]["record_id"] == "MAINT-0001"

    dates = [record["date"] for record in result["records"]]
    assert dates == sorted(dates, reverse=True)


def test_get_asset_with_no_maintenance_history():
    result = get_maintenance_history("ASSET-NO-HISTORY")

    assert result == {
        "asset_id": "ASSET-NO-HISTORY",
        "record_count": 0,
        "records": [],
    }


@pytest.mark.parametrize("asset_id", ["", "   ", None, 123])
def test_get_maintenance_history_invalid_input(asset_id):
    result = get_maintenance_history(asset_id)

    assert result == {"error": "asset_id must be a non-empty string"}
