"""Tests for maintenance-window facts extracted from investigation evidence."""

import pytest

from agent.bedrock.evidence_record import build_evidence_record
from agent.bedrock.operational_facts import extract_maintenance_window_facts


def test_extract_unavailable_maintenance_window():
    reference_timestamp = "2026-11-10T18:00:00Z"
    asset_id = "CONV-MTR-042"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": asset_id},
        result={
            "asset_id": asset_id,
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": reference_timestamp,
            "maintenance_window": {
                "available": False,
                "reason": "No upcoming maintenance window found",
            },
        },
    )

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": True,
        "facts": {
            "asset_id": asset_id,
            "reference_timestamp": reference_timestamp,
            "maintenance_window_available": False,
        },
    }


def test_reject_maintenance_window_timestamp_mismatch():
    asset_id = "CONV-MTR-042"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": asset_id},
        result={
            "asset_id": asset_id,
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": "2026-11-09T14:30:00Z",
            "maintenance_window": {
                "available": True,
                "reason": "Upcoming maintenance window found",
            },
        },
    )

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result == {
        "valid": False,
        "reason": "maintenance-window timestamp mismatch",
    }


def test_reject_maintenance_window_asset_mismatch():
    reference_timestamp = "2026-11-10T18:00:00Z"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": "CONV-MTR-042"},
        result={
            "asset_id": "OTHER-ASSET",
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": reference_timestamp,
            "maintenance_window": {
                "available": False,
                "reason": "No upcoming maintenance window found",
            },
        },
    )

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id="CONV-MTR-042",
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": False,
        "reason": "maintenance-window result asset mismatch",
    }


def test_reject_duplicate_maintenance_window_records():
    asset_id = "CONV-MTR-042"
    reference_timestamp = "2026-11-10T18:00:00Z"

    window_result = {
        "asset_id": asset_id,
        "line_id": "PACKAGING-LINE-2",
        "reference_timestamp": reference_timestamp,
        "maintenance_window": {
            "available": False,
            "reason": "No upcoming maintenance window found",
        },
    }

    records = [
        build_evidence_record(
            tool_name="get_maintenance_window_status",
            tool_use_id=tool_use_id,
            identifiers={"asset_id": asset_id},
            result=window_result,
        )
        for tool_use_id in ("tool-window-001", "tool-window-002")
    ]

    result = extract_maintenance_window_facts(
        evidence_records=records,
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": False,
        "reason": "exactly one maintenance-window evidence record is required",
    }


def test_reject_tampered_maintenance_window_evidence():
    asset_id = "CONV-MTR-042"
    reference_timestamp = "2026-11-10T18:00:00Z"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": asset_id},
        result={
            "asset_id": asset_id,
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": reference_timestamp,
            "maintenance_window": {
                "available": False,
                "reason": "No upcoming maintenance window found",
            },
        },
    )

    # Simulate evidence modification after its digest was calculated.
    record["result"]["maintenance_window"]["available"] = True

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": False,
        "reason": "maintenance-window evidence integrity check failed",
    }


@pytest.mark.parametrize("digest", [None, "", "invalid-digest"])
def test_reject_missing_or_invalid_evidence_digest(digest):
    asset_id = "CONV-MTR-042"
    reference_timestamp = "2026-11-10T18:00:00Z"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": asset_id},
        result={
            "asset_id": asset_id,
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": reference_timestamp,
            "maintenance_window": {
                "available": False,
                "reason": "No upcoming maintenance window found",
            },
        },
    )

    if digest is None:
        del record["sha256"]
    else:
        record["sha256"] = digest

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": False,
        "reason": "maintenance-window evidence integrity check failed",
    }


@pytest.mark.parametrize(
    "availability",
    ["false", "true", 0, 1, None, []],
)
def test_reject_invalid_maintenance_window_availability(availability):
    asset_id = "CONV-MTR-042"
    reference_timestamp = "2026-11-10T18:00:00Z"

    record = build_evidence_record(
        tool_name="get_maintenance_window_status",
        tool_use_id="tool-window-001",
        identifiers={"asset_id": asset_id},
        result={
            "asset_id": asset_id,
            "line_id": "PACKAGING-LINE-2",
            "reference_timestamp": reference_timestamp,
            "maintenance_window": {
                "available": availability,
                "reason": "No upcoming maintenance window found",
            },
        },
    )

    result = extract_maintenance_window_facts(
        evidence_records=[record],
        expected_asset_id=asset_id,
        execution_context={
            "reference_timestamp": reference_timestamp,
        },
    )

    assert result == {
        "valid": False,
        "reason": "maintenance-window availability is invalid",
    }
