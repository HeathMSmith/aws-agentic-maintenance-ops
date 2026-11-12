"""Run one explicitly requested Bedrock Converse smoke test."""

from agent.bedrock.live_client import create_live_bedrock_client


MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

ROLE_ARN = (
    "arn:aws:iam::291634988692:"
    "role/bedrock-agent-lab-execution-role"
)


def main() -> None:
    """Verify a single live Bedrock Converse invocation."""

    client = create_live_bedrock_client(
        profile_name="portfolio",
        role_arn=ROLE_ARN,
    )

    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "Reply with one short sentence confirming "
                            "that this Bedrock Converse request succeeded."
                        )
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 64,
            "temperature": 0,
        },
    )

    print("Stop reason:", response["stopReason"])

    for block in response["output"]["message"]["content"]:
        if "text" in block:
            print("Model response:", block["text"])

    usage = response.get("usage", {})

    print("Input tokens:", usage.get("inputTokens"))
    print("Output tokens:", usage.get("outputTokens"))


if __name__ == "__main__":
    main()
