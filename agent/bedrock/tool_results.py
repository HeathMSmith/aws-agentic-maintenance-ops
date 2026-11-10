"""Build Converse API messages from local tool execution results."""

from agent.bedrock.tool_dispatcher import dispatch_tool


def build_tool_result_message(
    tool_use: dict,
    execution_context: dict | None = None,
) -> dict:
    """Execute a requested tool and return a Converse-compatible user message."""

    tool_use_id = tool_use["toolUseId"]
    tool_name = tool_use["name"]
    tool_input = tool_use["input"]

    result = dispatch_tool(tool_name, tool_input, execution_context)

    status = "error" if "error" in result else "success"

    return {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [
                        {
                            "json": result,
                        }
                    ],
                    "status": status,
                }
            }
        ],
    }
