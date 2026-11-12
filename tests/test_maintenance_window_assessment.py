
"""Tests for deterministic maintenance-window assessments."""

from agent.bedrock.maintenance_window_assessment import (
    build_maintenance_window_assessment,
)


def test_assessment_reports_no_available_window():
    operational_facts = {
        "asset_id": "CONV-MTR-042",
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "maintenance_window_available": False,
    }

    result = build_maintenance_window_assessment(operational_facts)

    assert result == {
        "available": False,
        "reference_timestamp": "2026-11-10T18:00:00Z",
        "summary": (
            "No active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        ),
    }


def test_assessment_reports_available_window():
    operational_facts = {
        "asset_id": "CONV-MTR-042",
        "reference_timestamp": "2026-11-09T18:00:00Z",
        "maintenance_window_available": True,
    }

    result = build_maintenance_window_assessment(operational_facts)

    assert result == {
        "available": True,
        "reference_timestamp": "2026-11-09T18:00:00Z",
        "summary": (
            "An active or upcoming maintenance window was found "
            "in the recorded production schedule at the investigation "
            "reference time."
        ),
    }
