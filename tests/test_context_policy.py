from copy import deepcopy

import pytest

from simulation.investigate_incident import investigate_incident
from simulation.policies.context_policy import evaluate_action_with_context


@pytest.fixture
def investigation():
    """Return an isolated investigation context for each test."""
    return deepcopy(investigate_incident("ALERT-0001"))


@pytest.mark.parametrize("severity", ["warning", "critical"])
def test_high_criticality_monitoring_requires_approval(investigation, severity):
    investigation["alert"]["severity"] = severity

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result == {
        "action": "continue_monitoring",
        "decision": "requires_approval",
        "reason": "High-criticality asset requires expert review",
    }


def test_low_criticality_monitoring_permitted(investigation):
    investigation["asset"]["criticality"] = "low"

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result["decision"] == "permitted"


def test_expert_review_permitted(investigation):
    result = evaluate_action_with_context("request_expert_review", investigation)

    assert result["decision"] == "permitted"


@pytest.mark.parametrize(
    "action",
    [
        "create_maintenance_work_order",
        "request_equipment_shutdown",
    ],
)
def test_sensitive_actions_require_approval(investigation, action):
    result = evaluate_action_with_context(action, investigation)

    assert result["decision"] == "requires_approval"


def test_unsupported_action_rejected(investigation):
    result = evaluate_action_with_context("restart_motor", investigation)

    assert result["decision"] == "rejected"


def test_incomplete_investigation_rejected(investigation):
    investigation["status"] = "failed"

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result == {
        "decision": "rejected",
        "reason": "investigation is incomplete",
    }


@pytest.mark.parametrize("missing_field", ["alert", "asset"])
def test_missing_evidence_rejected(investigation, missing_field):
    investigation.pop(missing_field)

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result == {
        "decision": "rejected",
        "reason": f"missing or invalid evidence: {missing_field}",
    }


@pytest.mark.parametrize(
    "severity",
    [None, "unknown"],
)
def test_invalid_severity_rejected(investigation, severity):
    investigation["alert"]["severity"] = severity

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result["decision"] == "rejected"
    assert result["reason"] == "invalid or missing alert severity"


@pytest.mark.parametrize(
    "criticality",
    [None, "unknown"],
)
def test_invalid_criticality_rejected(investigation, criticality):
    investigation["asset"]["criticality"] = criticality

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result["decision"] == "rejected"
    assert result["reason"] == "invalid or missing asset criticality"


@pytest.mark.parametrize(
    "field",
    [
        "asset",
        "maintenance_history",
        "production_schedule",
    ],
)
def test_policy_rejects_mismatched_asset_references(investigation, field):
    investigation[field]["asset_id"] = "WRONG-ASSET"

    result = evaluate_action_with_context("continue_monitoring", investigation)

    assert result == {
        "decision": "rejected",
        "reason": f"asset_id mismatch: {field}",
    }


@pytest.mark.parametrize(
    "field",
    [
        "maintenance_history",
        "production_schedule",
        "maintenance_window",
    ],
)
def test_policy_rejects_missing_operational_evidence(investigation, field):
    investigation.pop(field)

    result = evaluate_action_with_context(
        "create_maintenance_work_order", investigation
    )

    assert result == {
        "decision": "rejected",
        "reason": f"missing or invalid evidence: {field}",
    }


def test_policy_rejects_mismatched_maintenance_record(investigation):
    investigation["maintenance_history"]["records"][0]["asset_id"] = "WRONG-ASSET"

    result = evaluate_action_with_context("request_expert_review", investigation)

    assert result == {
        "decision": "rejected",
        "reason": "maintenance history contains mismatched asset records",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("hours_until_start", 1.0),
        ("remaining_duration_hours", 2.0),
        ("schedule_id", "WRONG-WINDOW"),
    ],
)
def test_policy_rejects_inconsistent_maintenance_window(investigation, field, value):
    investigation["maintenance_window"][field] = value

    result = evaluate_action_with_context(
        "create_maintenance_work_order",
        investigation,
    )

    assert result == {
        "decision": "rejected",
        "reason": "maintenance window does not match production schedule",
    }


def test_policy_rejects_invalid_schedule_timestamp(investigation):
    investigation["production_schedule"]["schedule"][1]["end"] = "invalid-timestamp"

    result = evaluate_action_with_context(
        "create_maintenance_work_order",
        investigation,
    )

    assert result["decision"] == "rejected"
    assert result["reason"].startswith("invalid maintenance window evidence:")
