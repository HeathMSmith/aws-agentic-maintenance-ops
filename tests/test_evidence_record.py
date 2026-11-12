
"""Tests for auditable maintenance evidence records."""

import pytest

from agent.bedrock.evidence_record import build_evidence_record


def test_evidence_hash_is_independent_of_dictionary_key_order():
    first = {
        "asset_id": "CONV-MTR-042",
        "criticality": "high",
    }

    second = {
        "criticality": "high",
        "asset_id": "CONV-MTR-042",
    }

    record_a = build_evidence_record(
        "get_asset_context",
        "evidence-1",
        {"asset_id": "CONV-MTR-042"},
        first,
    )

    record_b = build_evidence_record(
        "get_asset_context",
        "evidence-2",
        {"asset_id": "CONV-MTR-042"},
        second,
    )

    assert record_a["sha256"] == record_b["sha256"]
    assert len(record_a["sha256"]) == 64


def test_evidence_snapshot_is_independent_of_original_data():
    evidence = {
        "asset_id": "CONV-MTR-042",
        "observations": {
            "temperature_c": 89.0,
        },
    }

    identifiers = {"asset_id": "CONV-MTR-042"}

    record = build_evidence_record(
        "get_asset_context",
        "evidence-1",
        identifiers,
        evidence,
    )

    evidence["observations"]["temperature_c"] = 25.0
    identifiers["asset_id"] = "OTHER-ASSET"

    assert record["result"]["observations"]["temperature_c"] == 89.0
    assert record["identifiers"]["asset_id"] == "CONV-MTR-042"


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_evidence_record_rejects_nonfinite_numbers(value):
    with pytest.raises(ValueError):
        build_evidence_record(
            "get_asset_context",
            "evidence-1",
            {"asset_id": "CONV-MTR-042"},
            {"rated_power_kw": value},
        )
