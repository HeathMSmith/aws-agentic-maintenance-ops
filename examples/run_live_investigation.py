"""Run a maintenance investigation using live Amazon Bedrock inference."""

import json

from agent.bedrock.investigation_workflow import run_investigation_workflow
from agent.bedrock.live_client import create_live_bedrock_client


MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

ROLE_ARN = (
    "arn:aws:iam::291634988692:"
    "role/bedrock-agent-lab-execution-role"
)


def main() -> None:
    """Execute a live Bedrock investigation against simulated local evidence."""

    client = create_live_bedrock_client(
        profile_name="portfolio",
        role_arn=ROLE_ARN,
    )

    result = run_investigation_workflow(
        client=client,
        model_id=MODEL_ID,
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    print(json.dumps(result, indent=2))

    if result["status"] != "evaluated":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
