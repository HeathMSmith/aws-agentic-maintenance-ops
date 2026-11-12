from agent.bedrock.tool_specs import (
    TOOL_CONFIG,
    MAINTENANCE_ACTION_EVALUATION_TOOL,
)


def test_maintenance_window_tool_schema():
    tools = {
        tool["toolSpec"]["name"]: tool["toolSpec"] for tool in TOOL_CONFIG["tools"]
    }

    assert len(tools) == 5

    schema = tools["get_maintenance_window_status"]["inputSchema"]["json"]

    assert schema["type"] == "object"
    assert schema["required"] == ["asset_id"]
    assert set(schema["properties"]) == {"asset_id"}
    assert schema["properties"]["asset_id"]["type"] == "string"
    assert schema["additionalProperties"] is False
    assert "reference_timestamp" not in schema["properties"]


def test_maintenance_action_evaluation_tool_schema():

    schema = MAINTENANCE_ACTION_EVALUATION_TOOL[
        "toolSpec"
    ]["inputSchema"]["json"]

    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"alert_id", "action"}
    assert set(schema["required"]) == {"alert_id", "action"}
    assert schema["additionalProperties"] is False

    assert schema["properties"]["alert_id"]["type"] == "string"
    assert schema["properties"]["action"]["type"] == "string"

    assert set(schema["properties"]["action"]["enum"]) == {
        "continue_monitoring",
        "request_expert_review",
        "create_maintenance_work_order",
        "request_equipment_shutdown",
    }


def test_investigation_exposes_only_evidence_tools():
    """The investigation model must not receive policy-evaluation tools."""

    tool_names = {tool["toolSpec"]["name"] for tool in TOOL_CONFIG["tools"]}

    assert tool_names == {
        "get_equipment_alert",
        "get_asset_context",
        "get_maintenance_history",
        "get_production_schedule",
        "get_maintenance_window_status",
    }
