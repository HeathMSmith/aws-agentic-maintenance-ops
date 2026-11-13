
"""Tests for deterministic maintenance authorization assessments."""

import pytest

from agent.bedrock.authorization_assessment import (
    build_authorization_assessment,
)


def test_shutdown_requires_approval():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "request_equipment_shutdown",
            "decision": "requires_approval",
        },
    }

    result = build_authorization_assessment(policy_result)

    assert result == {
        "action": "request_equipment_shutdown",
        "decision": "requires_approval",
        "summary": (
            "The proposed equipment shutdown requires approval "
            "before execution."
        ),
    }


def test_expert_review_is_permitted():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "request_expert_review",
            "decision": "permitted",
        },
    }

    result = build_authorization_assessment(policy_result)

    assert result == {
        "action": "request_expert_review",
        "decision": "permitted",
        "summary": (
            "The proposed expert review request is permitted "
            "under the simulation policy."
        ),
    }


def test_rejected_policy_evaluation_cannot_generate_assessment():
    policy_result = {
        "status": "rejected",
        "reason": "proposal alert_id does not match the requested incident",
    }

    with pytest.raises(
        ValueError,
        match="policy evaluation must be successful",
    ):
        build_authorization_assessment(policy_result)


def test_unknown_policy_decision_is_rejected():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "request_expert_review",
            "decision": "automatically_approved",
        },
    }

    with pytest.raises(
        ValueError,
        match="unsupported authorization assessment",
    ):
        build_authorization_assessment(policy_result)


def test_monitoring_requires_approval_when_policy_requires_it():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "continue_monitoring",
            "decision": "requires_approval",
        },
    }

    result = build_authorization_assessment(policy_result)

    assert result == {
        "action": "continue_monitoring",
        "decision": "requires_approval",
        "summary": (
            "The proposed continuation of monitoring requires "
            "approval under the simulation policy."
        ),
    }


def test_monitoring_is_permitted_when_policy_allows_it():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "continue_monitoring",
            "decision": "permitted",
        },
    }

    result = build_authorization_assessment(policy_result)

    assert result == {
        "action": "continue_monitoring",
        "decision": "permitted",
        "summary": (
            "The proposed continuation of monitoring is permitted "
            "under the simulation policy."
        ),
    }


def test_maintenance_work_order_requires_approval():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "create_maintenance_work_order",
            "decision": "requires_approval",
        },
    }

    result = build_authorization_assessment(policy_result)

    assert result == {
        "action": "create_maintenance_work_order",
        "decision": "requires_approval",
        "summary": (
            "The proposed maintenance work order requires approval "
            "before execution."
        ),
    }


def test_missing_policy_decision_is_rejected():
    policy_result = {
        "status": "evaluated",
    }

    with pytest.raises(
        ValueError,
        match="policy_decision must be a dictionary",
    ):
        build_authorization_assessment(policy_result)


def test_shutdown_cannot_be_reported_as_permitted():
    policy_result = {
        "status": "evaluated",
        "policy_decision": {
            "action": "request_equipment_shutdown",
            "decision": "permitted",
        },
    }

    with pytest.raises(
        ValueError,
        match="unsupported authorization assessment",
    ):
        build_authorization_assessment(policy_result)
