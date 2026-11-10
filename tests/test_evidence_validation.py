from copy import deepcopy

import pytest

from simulation.investigate_incident import investigate_incident
from simulation.policies.evidence_validation import validate_investigation_evidence


@pytest.fixture
def investigation():
    """Provide an isolated investigation for each test."""
    return deepcopy(investigate_incident("ALERT-0001"))


def test_valid_investigation(investigation):
    result = validate_investigation_evidence(investigation)

    assert result == {"valid": True}


def test_reject_incomplete_investigation(investigation):
    investigation["status"] = "failed"

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "investigation is incomplete",
    }


@pytest.mark.parametrize(
    "field",
    [
        "alert",
        "asset",
        "maintenance_history",
        "production_schedule",
        "maintenance_window",
    ],
)
def test_reject_missing_evidence(investigation, field):
    investigation.pop(field)

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": f"missing or invalid evidence: {field}",
    }


@pytest.mark.parametrize(
    "field",
    [
        "asset",
        "maintenance_history",
        "production_schedule",
    ],
)
def test_reject_mismatched_asset_id(investigation, field):
    investigation[field]["asset_id"] = "WRONG-ASSET"

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": f"asset_id mismatch: {field}",
    }


def test_reject_missing_alert_asset_id(investigation):
    investigation["alert"].pop("asset_id")

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "missing or invalid alert asset_id",
    }


def test_reject_invalid_maintenance_records(investigation):
    investigation["maintenance_history"]["records"] = None

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "invalid maintenance history records",
    }


def test_reject_mismatched_maintenance_record(investigation):
    investigation["maintenance_history"]["records"][0]["asset_id"] = "WRONG-ASSET"

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "maintenance history contains mismatched asset records",
    }


def test_accept_empty_maintenance_history(investigation):
    investigation["maintenance_history"]["records"] = []
    investigation["maintenance_history"]["record_count"] = 0

    result = validate_investigation_evidence(investigation)

    assert result == {"valid": True}


@pytest.mark.parametrize(
    "record_count",
    [
        99,  # Doesn't match the records list
        -1,  # Negative count
        None,  # Missing/null count
        "2",  # String instead of integer
        True,  # Boolean instead of integer
        2.0,  # Float instead of integer
    ],
)
def test_reject_invalid_maintenance_record_count(investigation, record_count):
    investigation["maintenance_history"]["record_count"] = record_count

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "maintenance history record count mismatch",
    }


def test_reject_missing_maintenance_record_count(investigation):
    investigation["maintenance_history"].pop("record_count")

    result = validate_investigation_evidence(investigation)

    assert result == {
        "valid": False,
        "reason": "maintenance history record count mismatch",
    }
