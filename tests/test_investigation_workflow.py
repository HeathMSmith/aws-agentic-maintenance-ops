from agent.bedrock.investigation_workflow import run_investigation_workflow

def make_evidence_tool_response():
    """Simulate Bedrock requesting all five required evidence tools."""

    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": f"evidence-{index}",
                            "name": tool_name,
                            "input": tool_input,
                        }
                    }
                    for index, (tool_name, tool_input) in enumerate(
                        [
                            ("get_equipment_alert", {"alert_id": "ALERT-0001"}),
                            ("get_asset_context", {"asset_id": "CONV-MTR-042"}),
                            (
                                "get_maintenance_history",
                                {"asset_id": "CONV-MTR-042"},
                            ),
                            (
                                "get_production_schedule",
                                {"asset_id": "CONV-MTR-042"},
                            ),
                            (
                                "get_maintenance_window_status",
                                {"asset_id": "CONV-MTR-042"},
                            ),
                        ],
                        start=1,
                    )
                ],
            }
        },
    }

def test_workflow_requires_approval_for_shutdown_proposal():
    class FakeClient:
        def __init__(self):
            self.calls = []
        def converse(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return make_evidence_tool_response()
            if len(self.calls) == 2:
                return {
                    "stopReason": "end_turn",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "text": (
                                        "Investigation complete. "
                                        "Immediate shutdown is authorized."
                                    )
                                }
                            ],
                        }
                    },
                }
            return {
                "stopReason": "tool_use",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "proposal-001",
                                    "name": "submit_maintenance_action_proposal",
                                    "input": {
                                        "alert_id": "ALERT-0001",
                                        "proposed_action": "request_equipment_shutdown",
                                        "reason": (
                                            "Elevated vibration and temperature "
                                            "require equipment inspection."
                                        ),
                                    },
                                }
                            }
                        ],
                    }
                },
            }

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "evaluated"
    assert len(client.calls) == 3

    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert result["proposal"]["proposed_action"] == "request_equipment_shutdown"

    policy = result["policy_result"]

    assert policy["status"] == "evaluated"
    assert policy["policy_decision"]["decision"] == "requires_approval"

    # The two Converse phases use separate tool configurations.
    assert len(client.calls[0]["toolConfig"]["tools"]) == 5
    assert len(client.calls[1]["toolConfig"]["tools"]) == 5
    assert len(client.calls[2]["toolConfig"]["tools"]) == 1

def test_workflow_rejects_incomplete_investigation():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return make_evidence_tool_response()

            return {
                "stopReason": "max_tokens",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"text": "Investigation incomplete."}
                        ],
                    }
                },
            }

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "investigation did not complete"

    assert result["investigation"]["status"] == "stopped"
    assert result["investigation"]["reason"] == "max_tokens"

    investigation = result["investigation"]

    trace = investigation["execution_trace"]
    records = investigation["evidence_records"]

    assert len(trace) == 5
    assert all(entry["status"] == "success" for entry in trace)

    assert len(records) == 5
    assert all(len(record["sha256"]) == 64 for record in records)

    # Two investigation calls; no proposal generation or policy evaluation.
    assert len(client.calls) == 2

    # Only investigation tools were available to the model.
    assert all(
        len(call["toolConfig"]["tools"]) == 5
        for call in client.calls
    )

    assert "proposal" not in result
    assert "policy_result" not in result

def test_workflow_rejects_invalid_action_proposal():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return make_evidence_tool_response()

            if len(self.calls) == 2:
                return {
                    "stopReason": "end_turn",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"text": "Investigation complete."}
                            ],
                        }
                    },
                }

            return {
                "stopReason": "tool_use",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "proposal-002",
                                    "name": "submit_maintenance_action_proposal",
                                    "input": {
                                        "alert_id": "ALERT-0001",
                                        "proposed_action": "restart_equipment",
                                        "reason": "Restart the motor immediately.",
                                    },
                                }
                            }
                        ],
                    }
                },
            }

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "rejected"
    assert result["reason"] == (
        "valid structured action proposal was not received"
    )

    assert result["proposal_result"] == {
        "status": "rejected",
        "reason": "unsupported proposed maintenance action",
    }

    assert len(client.calls) == 3

def test_workflow_rejects_mismatched_proposal_alert():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return make_evidence_tool_response()

            if len(self.calls) == 2:
                return {
                    "stopReason": "end_turn",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"text": "Investigation complete."}
                            ],
                        }
                    },
                }

            return {
                "stopReason": "tool_use",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "proposal-003",
                                    "name": "submit_maintenance_action_proposal",
                                    "input": {
                                        "alert_id": "ALERT-9999",
                                        "proposed_action": "request_equipment_shutdown",
                                        "reason": (
                                            "Elevated vibration and temperature "
                                            "require inspection."
                                        ),
                                    },
                                }
                            }
                        ],
                    }
                },
            }

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "rejected"

    assert result["policy_result"] == {
        "status": "rejected",
        "reason": "proposal alert_id does not match the requested incident",
    }

    assert result["proposal"]["alert_id"] == "ALERT-9999"
    assert len(client.calls) == 3

def test_workflow_rejects_mismatched_evidence_asset():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                response = make_evidence_tool_response()

                for block in response["output"]["message"]["content"]:
                    tool_use = block["toolUse"]

                    if tool_use["name"] == "get_maintenance_history":
                        tool_use["input"]["asset_id"] = "CONV-MTR-999"

                return response

            if len(self.calls) == 2:
                return {
                    "stopReason": "end_turn",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"text": "Investigation complete."}
                            ],
                        }
                    },
                }

            raise AssertionError(
                "Proposal generation must not occur for mismatched evidence"
            )

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "rejected"
    assert result["reason"] == (
        "investigation evidence identity is invalid"
    )

    assert result["identity_validation"][
        "missing_or_mismatched_tools"
    ] == ["get_maintenance_history"]

    assert len(client.calls) == 2

def test_workflow_rejects_mismatched_evidence_alert():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                response = make_evidence_tool_response()

                for block in response["output"]["message"]["content"]:
                    tool_use = block["toolUse"]

                    if tool_use["name"] == "get_equipment_alert":
                        tool_use["input"]["alert_id"] = "ALERT-9999"

                return response

            if len(self.calls) == 2:
                return {
                    "stopReason": "end_turn",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"text": "Investigation complete."}
                            ],
                        }
                    },
                }

            raise AssertionError(
                "Proposal generation must not occur for mismatched alert evidence"
            )

    client = FakeClient()

    result = run_investigation_workflow(
        client=client,
        model_id="test-model",
        alert_id="ALERT-0001",
        execution_context={
            "reference_timestamp": "2026-11-10T18:00:00Z",
        },
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "investigation evidence is incomplete"

    assert result["evidence_validation"]["missing_tools"] == [
        "get_equipment_alert"
    ]

    assert len(client.calls) == 2
