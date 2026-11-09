import pytest

from agent.tools.asset_context import get_asset_context


def test_get_existing_asset():
    result = get_asset_context("CONV-MTR-042")

    assert result["asset_id"] == "CONV-MTR-042"
    assert result["criticality"] == "high"
    assert result["operational_status"] == "running"


def test_get_nonexistent_asset():
    result = get_asset_context("INVALID-ASSET")

    assert result == {"error": "Asset not found: INVALID-ASSET"}


@pytest.mark.parametrize("asset_id", ["", "   ", None, 123])
def test_get_asset_invalid_input(asset_id):
    result = get_asset_context(asset_id)

    assert result == {"error": "asset_id must be a non-empty string"}
