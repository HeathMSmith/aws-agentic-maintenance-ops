"""Tests for the live Bedrock investigation entry point."""

import pytest

from examples import run_live_investigation


def test_live_investigation_entry_point(monkeypatch, capsys):
    """Verify live configuration without making AWS API calls."""

    calls = {}
    fake_client = object()

    def fake_create_client(**kwargs):
        calls["client_config"] = kwargs
        return fake_client

    def fake_workflow(**kwargs):
        calls["workflow_config"] = kwargs
        return {
            "status": "evaluated",
            "policy_result": {
                "policy_decision": {
                    "decision": "requires_approval",
                },
            },
        }

    monkeypatch.setattr(
        run_live_investigation,
        "create_live_bedrock_client",
        fake_create_client,
    )

    monkeypatch.setattr(
        run_live_investigation,
        "run_investigation_workflow",
        fake_workflow,
    )

    run_live_investigation.main()

    assert calls["client_config"] == {
        "profile_name": "portfolio",
        "role_arn": run_live_investigation.ROLE_ARN,
    }

    assert calls["workflow_config"] == {
        "client": fake_client,
        "model_id": run_live_investigation.MODEL_ID,
        "alert_id": "ALERT-0001",
        "execution_context": {
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    }

    output = capsys.readouterr().out

    assert '"status": "evaluated"' in output
    assert '"decision": "requires_approval"' in output


def test_live_investigation_rejected_result(monkeypatch):
    """An unsuccessful investigation must exit with a nonzero status."""

    monkeypatch.setattr(
        run_live_investigation,
        "create_live_bedrock_client",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        run_live_investigation,
        "run_investigation_workflow",
        lambda **kwargs: {
            "status": "rejected",
            "reason": "investigation did not complete",
        },
    )

    with pytest.raises(SystemExit) as exc:
        run_live_investigation.main()

    assert exc.value.code == 1
