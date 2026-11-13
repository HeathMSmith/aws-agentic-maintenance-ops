
"""Run a scripted maintenance investigation without AWS API calls."""

import json

from agent.bedrock.investigation_workflow import run_investigation_workflow
from examples.offline_bedrock_client import OfflineBedrockClient


def main() -> None:
    """Execute and display the offline investigation workflow."""

    client = OfflineBedrockClient()

    result = run_investigation_workflow(
        client=client,
        model_id="offline-demo",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    summary = {
        "workflow_status": result["status"],
        "converse_calls": len(client.calls),
    }

    if result["status"] == "evaluated":
        summary.update(
            {
                "investigation": result["investigation"]["text"],
                "investigation_text_status": result["investigation_text_status"],
                "execution_trace": result["investigation"]["execution_trace"],
                "evidence_records": result["investigation"]["evidence_records"],
                "operational_facts": result["operational_facts"],
                "maintenance_window_assessment": result["maintenance_window_assessment"],
                "proposal": result["proposal"],
                "proposal_reason_status": result["proposal_reason_status"],
                "authorization_assessment": result["authorization_assessment"],
                "policy_decision": result["policy_result"]["policy_decision"],
                "decision_summary": {
                    "maintenance_window_assessment": result[
                        "maintenance_window_assessment"
                    ],
                    "authorization_assessment": result["authorization_assessment"],
                },
            }
        )
    else:
        summary["result"] = result

    print(json.dumps(summary, indent=2))

    if result["status"] != "evaluated":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
