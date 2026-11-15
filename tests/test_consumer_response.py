
"""Tests for consumer-facing maintenance investigation responses."""

import pytest

from agent.bedrock.consumer_response import rejected_response


def test_rejected_response():
    """Return the expected standardized rejection structure."""

    assert rejected_response("investigation_failed") == {
        "status": "rejected",
        "reason": "investigation_failed",
    }

@pytest.mark.parametrize(
    "result",
    [
        None,
        [],
        "unexpected response",
        {},
        {"reason": "missing status"},
        {"status": "unknown"},
    ],
)
def test_is_valid_workflow_status_rejects_malformed_results(result):
    """Reject malformed workflow status structures."""

    from agent.bedrock.consumer_response import is_valid_workflow_status

    assert is_valid_workflow_status(result) is False


@pytest.mark.parametrize("status", ["evaluated", "rejected"])
def test_is_valid_workflow_status_accepts_known_statuses(status):
    """Accept recognized workflow statuses."""

    from agent.bedrock.consumer_response import is_valid_workflow_status

    assert is_valid_workflow_status({"status": status}) is True

def test_is_valid_authorization_assessment():
    """Validate authorization against the canonical policy assessment."""

    from agent.bedrock.consumer_response import (
        is_valid_authorization_assessment,
    )

    valid_assessment = {
        "action": "request_equipment_shutdown",
        "decision": "requires_approval",
        "summary": (
            "The proposed equipment shutdown requires approval "
            "before execution."
        ),
    }

    assert is_valid_authorization_assessment(
        valid_assessment,
        "request_equipment_shutdown",
    ) is True

    assert is_valid_authorization_assessment(
        valid_assessment,
        "request_expert_review",
    ) is False

    assert is_valid_authorization_assessment(
        {
            **valid_assessment,
            "decision": "permitted",
        },
        "request_equipment_shutdown",
    ) is False

    assert is_valid_authorization_assessment(
        {
            **valid_assessment,
            "summary": "Shutdown has already been approved.",
        },
        "request_equipment_shutdown",
    ) is False

    assert is_valid_authorization_assessment(
        None,
        "request_equipment_shutdown",
    ) is False

def test_is_valid_maintenance_window_assessment():
    """Validate maintenance-window fields, summary, and reference timestamp."""

    from agent.bedrock.consumer_response import (
        is_valid_maintenance_window_assessment,
    )

    timestamp = "2026-11-10T18:00:00Z"

    valid_assessment = {
        "available": False,
        "reference_timestamp": timestamp,
        "summary": (
            "No active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        ),
    }

    assert is_valid_maintenance_window_assessment(
        valid_assessment, timestamp
    ) is True

    assert is_valid_maintenance_window_assessment(
        {**valid_assessment, "available": "false"}, timestamp
    ) is False

    assert is_valid_maintenance_window_assessment(
        {**valid_assessment, "summary": "A maintenance window is available."},
        timestamp,
    ) is False

    assert is_valid_maintenance_window_assessment(
        valid_assessment, "2026-11-11T18:00:00Z"
    ) is False

    assert is_valid_maintenance_window_assessment(
        None, timestamp
    ) is False

@pytest.mark.parametrize(
    "proposal",
    [
        None,
        [],
        {},
        {"proposed_action": None},
        {"proposed_action": 123},
        {"proposed_action": ""},
        {"proposed_action": "   "},
    ],
)
def test_is_valid_proposal_action_rejects_invalid_input(proposal):
    """Reject proposals without a usable action identifier."""

    from agent.bedrock.consumer_response import is_valid_proposal_action

    assert is_valid_proposal_action(proposal) is False


def test_is_valid_proposal_action_accepts_valid_input():
    """Accept a proposal containing a non-empty action identifier."""

    from agent.bedrock.consumer_response import is_valid_proposal_action

    assert is_valid_proposal_action(
        {"proposed_action": "request_equipment_shutdown"}
    ) is True

def test_evaluated_response():
    """Format validated assessments without model-generated reasoning."""

    from agent.bedrock.consumer_response import evaluated_response

    window_assessment = {
        "available": False,
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "summary": "No active or upcoming maintenance window was found.",
    }

    authorization_assessment = {
        "action": "request_equipment_shutdown",
        "decision": "requires_approval",
        "summary": "Shutdown requires approval.",
    }

    result = evaluated_response(
        alert_id="ALERT-0001",
        window_assessment=window_assessment,
        authorization_assessment=authorization_assessment,
        proposed_action="request_equipment_shutdown",
    )

    assert result == {
        "status": "evaluated",
        "alert_id": "ALERT-0001",
        "decision_summary": {
            "maintenance_window_assessment": window_assessment,
            "authorization_assessment": authorization_assessment,
        },
        "proposal": {
            "action": "request_equipment_shutdown",
            "provenance": "model_generated_unverified",
        },
    }
