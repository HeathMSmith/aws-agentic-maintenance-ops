from agent.bedrock.tool_specs import TOOL_CONFIG


def test_maintenance_window_tool_schema():
    tools = {
        tool["toolSpec"]["name"]: tool["toolSpec"]
        for tool in TOOL_CONFIG["tools"]
    }

    assert len(tools) == 5

    schema = tools["get_maintenance_window_status"]["inputSchema"]["json"]

    assert schema["type"] == "object"
    assert schema["required"] == ["asset_id"]
    assert set(schema["properties"]) == {"asset_id"}
    assert schema["properties"]["asset_id"]["type"] == "string"
    assert schema["additionalProperties"] is False
    assert "reference_timestamp" not in schema["properties"]
