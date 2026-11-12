"""Build auditable records from validated maintenance evidence."""

import copy
import hashlib
import json


def build_evidence_record(
    tool_name: str,
    tool_use_id: str,
    identifiers: dict,
    result: dict,
) -> dict:
    """Create an evidence record with a deterministic content digest."""
    record = {
        "tool_name": tool_name,
        "tool_use_id": tool_use_id,
        "identifiers": copy.deepcopy(identifiers),
        "result": copy.deepcopy(result),
    }

    canonical_json = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    digest = hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()

    return {
        **record,
        "sha256": digest,
    }
