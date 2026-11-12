
"""Extract authoritative operational facts from investigation evidence."""

from agent.bedrock.evidence_record import build_evidence_record


def extract_maintenance_window_facts(
    evidence_records: list,
    expected_asset_id: str,
    execution_context: dict,
) -> dict:
    """Extract maintenance-window facts for the investigated asset and time."""

    if not isinstance(evidence_records, list):
        return {"valid": False, "reason": "evidence records must be a list"}

    if not isinstance(expected_asset_id, str) or not expected_asset_id.strip():
        return {"valid": False, "reason": "expected asset_id is invalid"}

    if not isinstance(execution_context, dict):
        return {"valid": False, "reason": "execution context must be a dictionary"}

    reference_timestamp = execution_context.get("reference_timestamp")

    if not isinstance(reference_timestamp, str) or not reference_timestamp.strip():
        return {"valid": False, "reason": "reference timestamp is invalid"}

    records = [
        record
        for record in evidence_records
        if isinstance(record, dict)
        and record.get("tool_name") == "get_maintenance_window_status"
    ]

    if len(records) != 1:
        return {
            "valid": False,
            "reason": "exactly one maintenance-window evidence record is required",
        }

    record = records[0]

    try:
        reconstructed = build_evidence_record(
            tool_name=record["tool_name"],
            tool_use_id=record["tool_use_id"],
            identifiers=record["identifiers"],
            result=record["result"],
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return {
            "valid": False,
            "reason": "maintenance-window evidence integrity check failed",
        }

    if reconstructed["sha256"] != record.get("sha256"):
        return {
            "valid": False,
            "reason": "maintenance-window evidence integrity check failed",
        }

    result = record.get("result")

    if not isinstance(result, dict):
        return {"valid": False, "reason": "maintenance-window result is invalid"}

    if record.get("identifiers") != {"asset_id": expected_asset_id}:
        return {"valid": False, "reason": "maintenance-window request asset mismatch"}

    if result.get("asset_id") != expected_asset_id:
        return {"valid": False, "reason": "maintenance-window result asset mismatch"}

    if result.get("reference_timestamp") != reference_timestamp:
        return {"valid": False, "reason": "maintenance-window timestamp mismatch"}

    window = result.get("maintenance_window")

    if not isinstance(window, dict):
        return {"valid": False, "reason": "maintenance-window data is invalid"}

    if type(window.get("available")) is not bool:
        return {"valid": False, "reason": "maintenance-window availability is invalid"}

    return {
        "valid": True,
        "facts": {
            "asset_id": expected_asset_id,
            "reference_timestamp": reference_timestamp,
            "maintenance_window_available": window["available"],
        },
    }
