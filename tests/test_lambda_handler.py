
"""Tests for the AWS Lambda investigation entry point."""

import pytest


@pytest.mark.parametrize(
    "event",
    [
        {},
        {"alert_id": ""},
        {"alert_id": "   "},
        {"alert_id": None},
        {"alert_id": 123},
        {"alert_id": "ALERT-0001", "reference_timestamp": "invalid"},
        {"alert_id": "ALERT-0001", "reference_timestamp": "2026-11-10T18:00:00"},
    ],
)
def test_lambda_handler_rejects_invalid_input(event):
    """Invalid invocation input must be rejected before AWS initialization."""

    from lambda_handler import lambda_handler

    result = lambda_handler(event, None)

    assert result["status"] == "rejected"
    assert result["reason"] == "invalid_invocation_input"


def test_lambda_handler_accepts_valid_input(monkeypatch):
    """Valid input must pass normalized context to the investigation."""

    import lambda_handler as handler_module

    from unittest.mock import Mock

    mock_client = Mock()
    captured = {}

    def fake_workflow(**kwargs):
        captured.update(kwargs)
        return {
            "status": "rejected",
            "reason": "simulated_workflow_rejection",
        }

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        fake_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T13:00:00-05:00",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "investigation_failed",
    }
    assert captured["client"] is mock_client
    assert captured["alert_id"] == "ALERT-0001"
    assert captured["execution_context"] == {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }

def test_lambda_handler_rejects_null_timestamp():
    """An explicitly null timestamp must not be treated as omitted."""

    from lambda_handler import lambda_handler

    result = lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": None,
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_invocation_input",
    }


def test_lambda_handler_generates_timestamp_when_omitted(monkeypatch):
    """Omitted timestamp must produce a valid UTC execution context."""

    from datetime import datetime, timezone
    from unittest.mock import Mock

    import lambda_handler as handler_module

    captured = {}
    mock_client = Mock()

    def fake_workflow(**kwargs):
        captured.update(kwargs)
        return {
            "status": "rejected",
            "reason": "simulated_workflow_rejection",
        }

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        fake_workflow,
    )

    before = datetime.now(timezone.utc)

    result = handler_module.lambda_handler(
        {"alert_id": "ALERT-0001"},
        None,
    )

    after = datetime.now(timezone.utc)

    assert result == {
        "status": "rejected",
        "reason": "investigation_failed",
    }

    assert captured["client"] is mock_client
    assert captured["alert_id"] == "ALERT-0001"

    timestamp = captured["execution_context"]["reference_timestamp"]

    assert timestamp.endswith("Z")

    parsed = datetime.fromisoformat(timestamp)

    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0
    assert before <= parsed <= after

def test_invalid_input_does_not_initialize_bedrock(monkeypatch):
    """Invalid invocations must be rejected before AWS initialization."""

    import lambda_handler as handler_module

    def forbidden_bedrock_initialization(*args, **kwargs):
        raise AssertionError(
            "Bedrock client must not be initialized for invalid input"
        )

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        forbidden_bedrock_initialization,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_invocation_input",
    }

def test_lambda_handler_invokes_investigation_workflow(monkeypatch):
    """Valid input must invoke the investigation with trusted context."""

    import lambda_handler as handler_module

    from unittest.mock import Mock

    mock_client = Mock()
    workflow_calls = []

    def fake_client_factory():
        return mock_client

    def fake_workflow(**kwargs):
        workflow_calls.append(kwargs)
        return {
            "status": "rejected",
            "reason": "simulated_workflow_rejection",
        }

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        fake_client_factory,
        raising=False,
    )
    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        fake_workflow,
        raising=False,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T13:00:00-05:00",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "investigation_failed",
    }

    assert len(workflow_calls) == 1
    assert workflow_calls[0]["client"] is mock_client
    assert workflow_calls[0]["alert_id"] == "ALERT-0001"
    assert workflow_calls[0]["execution_context"] == {
        "reference_timestamp": "2026-11-10T18:00:00Z",
    }

def test_lambda_handler_returns_safe_decision_summary(monkeypatch):
    """Expose policy assessments without unverified model narrative."""

    from unittest.mock import Mock

    import lambda_handler as handler_module

    mock_client = Mock()

    window_assessment = {
        "available": False,
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "summary": (
            "No active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        ),
    }

    authorization_assessment = {
        "action": "request_equipment_shutdown",
        "decision": "requires_approval",
        "summary": (
            "The proposed equipment shutdown requires approval "
            "before execution."
        ),
    }

    def fake_workflow(**kwargs):
        return {
            "status": "evaluated",
            "investigation": {
                "text": "Immediate shutdown is authorized.",
            },
            "investigation_text_status": "model_generated_unverified",
            "maintenance_window_assessment": window_assessment,
            "authorization_assessment": authorization_assessment,
            "proposal": {
                "alert_id": "ALERT-0001",
                "proposed_action": "request_equipment_shutdown",
                "reason": "Shutdown is already authorized.",
            },
            "proposal_reason_status": "model_generated_unverified",
        }

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        fake_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
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

def test_lambda_handler_rejects_incomplete_evaluation(monkeypatch):
    """An evaluated workflow without authorization must be rejected."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def incomplete_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "No maintenance window available.",
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
            # Authorization assessment deliberately missing.
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        incomplete_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_rejects_mismatched_authorization(monkeypatch):
    """Authorization must describe the same action as the proposal."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def inconsistent_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "No maintenance window available.",
            },
            "authorization_assessment": {
                "action": "request_expert_review",
                "decision": "permitted",
                "summary": "Expert review is permitted.",
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        inconsistent_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

@pytest.mark.parametrize(
    "invalid_authorization",
    [
        {
            "action": "request_equipment_shutdown",
        },
        {
            "action": "request_equipment_shutdown",
            "decision": None,
            "summary": "Approval required.",
        },
        {
            "action": "request_equipment_shutdown",
            "decision": "requires_approval",
            "summary": "",
        },
    ],
)
def test_lambda_handler_rejects_invalid_authorization_fields(
    monkeypatch, invalid_authorization
):
    """Reject evaluations with incomplete authorization assessments."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def invalid_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "No maintenance window available.",
            },
            "authorization_assessment": invalid_authorization,
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        invalid_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_rejects_unsupported_authorization_decision(monkeypatch):
    """Reject authorization decisions unsupported by deterministic policy."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def invalid_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "No maintenance window available.",
            },
            "authorization_assessment": {
                "action": "request_equipment_shutdown",
                "decision": "permitted",
                "summary": "Shutdown is permitted.",
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        invalid_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_rejects_inconsistent_authorization_summary(monkeypatch):
    """Reject authorization summaries that contradict policy decisions."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def inconsistent_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "No maintenance window available.",
            },
            "authorization_assessment": {
                "action": "request_equipment_shutdown",
                "decision": "requires_approval",
                "summary": "Shutdown has already been approved.",
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        inconsistent_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_rejects_inconsistent_maintenance_window_summary(
    monkeypatch,
):
    """Reject maintenance-window summaries that contradict availability."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def inconsistent_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-10T18:00:00Z",
                "summary": "A maintenance window is available.",
            },
            "authorization_assessment": {
                "action": "request_equipment_shutdown",
                "decision": "requires_approval",
                "summary": (
                    "The proposed equipment shutdown requires approval "
                    "before execution."
                ),
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        inconsistent_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_rejects_mismatched_assessment_timestamp(monkeypatch):
    """Reject assessments evaluated against a different reference time."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def inconsistent_workflow(**kwargs):
        return {
            "status": "evaluated",
            "maintenance_window_assessment": {
                "available": False,
                "reference_timestamp": "2026-11-11T18:00:00Z",
                "summary": (
                    "No active or upcoming maintenance window was found "
                    "in the recorded production schedule at the investigation "
                    "reference time."
                ),
            },
            "authorization_assessment": {
                "action": "request_equipment_shutdown",
                "decision": "requires_approval",
                "summary": (
                    "The proposed equipment shutdown requires approval "
                    "before execution."
                ),
            },
            "proposal": {
                "proposed_action": "request_equipment_shutdown",
            },
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        inconsistent_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

@pytest.mark.parametrize(
    "malformed_result",
    [
        None,
        [],
        "unexpected response",
        {},
        {"reason": "missing status"},
    ],
)
def test_lambda_handler_rejects_malformed_workflow_result(
    monkeypatch, malformed_result
):
    """Reject malformed workflow responses without raising exceptions."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        lambda **kwargs: malformed_result,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "invalid_workflow_result",
    }

def test_lambda_handler_sanitizes_workflow_rejection_reason(monkeypatch):
    """Do not expose internal workflow diagnostics to Lambda consumers."""

    import lambda_handler as handler_module

    monkeypatch.setattr(
        handler_module,
        "create_bedrock_runtime_client",
        lambda: object(),
    )

    def rejected_workflow(**kwargs):
        return {
            "status": "rejected",
            "reason": (
                "Internal Bedrock failure: diagnostic details "
                "must not be exposed."
            ),
        }

    monkeypatch.setattr(
        handler_module,
        "run_investigation_workflow",
        rejected_workflow,
    )

    result = handler_module.lambda_handler(
        {
            "alert_id": "ALERT-0001",
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
        None,
    )

    assert result == {
        "status": "rejected",
        "reason": "investigation_failed",
    }
