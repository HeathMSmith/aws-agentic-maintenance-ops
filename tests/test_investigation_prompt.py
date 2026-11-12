"""Tests for maintenance investigation prompt generation."""

from agent.bedrock.investigation_prompt import build_investigation_prompt
from agent.bedrock.evidence_completeness import REQUIRED_EVIDENCE_TOOLS


def test_investigation_prompt_includes_required_evidence():
    """The prompt must identify the alert and all required evidence tools."""

    alert_id = "ALERT-0001"

    prompt = build_investigation_prompt(alert_id)

    assert f"Investigate equipment alert {alert_id}" in prompt

    for tool_name in REQUIRED_EVIDENCE_TOOLS:
        assert tool_name in prompt

    assert "asset_id" in prompt
    assert "all five evidence" in prompt


def test_investigation_prompt_prohibits_authorization_claims():
    """Investigation instructions must not grant operational authority."""

    prompt = build_investigation_prompt("ALERT-0001")

    assert "Do not claim" in prompt
    assert "authorized" in prompt
    assert "not approve operational actions" in prompt
