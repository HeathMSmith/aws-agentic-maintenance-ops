from agent.bedrock.proposal_response import PROPOSAL_TOOL_NAME
from agent.bedrock.proposal_tool_spec import PROPOSAL_TOOL_CONFIG
from agent.bedrock.tool_specs import TOOL_CONFIG


def test_proposal_tool_configuration():
    tools = PROPOSAL_TOOL_CONFIG["tools"]

    assert len(tools) == 1

    spec = tools[0]["toolSpec"]

    assert spec["name"] == PROPOSAL_TOOL_NAME

    assert PROPOSAL_TOOL_CONFIG["toolChoice"] == {
        "tool": {"name": PROPOSAL_TOOL_NAME}
    }


def test_proposal_tool_input_schema():
    schema = PROPOSAL_TOOL_CONFIG["tools"][0]["toolSpec"][
        "inputSchema"
    ]["json"]

    assert schema["type"] == "object"

    assert set(schema["required"]) == {
        "alert_id",
        "proposed_action",
        "reason",
    }

    assert set(schema["properties"]) == set(schema["required"])
    assert schema["additionalProperties"] is False

    assert schema["properties"]["alert_id"]["type"] == "string"
    assert schema["properties"]["proposed_action"]["type"] == "string"
    assert schema["properties"]["reason"]["type"] == "string"


def test_proposal_tool_action_enum_matches_policy():
    from simulation.policies.maintenance_policy import ALLOWED_ACTIONS

    schema = PROPOSAL_TOOL_CONFIG["tools"][0]["toolSpec"][
        "inputSchema"
    ]["json"]

    supported_actions = schema["properties"]["proposed_action"]["enum"]

    assert set(supported_actions) == set(ALLOWED_ACTIONS)


def test_proposal_tool_is_separate_from_investigation_tools():
    investigation_names = {
        tool["toolSpec"]["name"]
        for tool in TOOL_CONFIG["tools"]
    }

    proposal_names = {
        tool["toolSpec"]["name"]
        for tool in PROPOSAL_TOOL_CONFIG["tools"]
    }

    assert len(investigation_names) == 6
    assert proposal_names == {PROPOSAL_TOOL_NAME}
    assert investigation_names.isdisjoint(proposal_names)
