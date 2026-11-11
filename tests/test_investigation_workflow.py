from agent.bedrock.investigation_workflow import run_investigation_workflow


def test_workflow_requires_approval_for_shutdown_proposal():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
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
    assert len(client.calls) == 2

    assert result["proposal"]["alert_id"] == "ALERT-0001"
    assert result["proposal"]["proposed_action"] == "request_equipment_shutdown"

    policy = result["policy_result"]

    assert policy["status"] == "evaluated"
    assert policy["policy_decision"]["decision"] == "requires_approval"

    # The two Converse phases use separate tool configurations.
    assert len(client.calls[0]["toolConfig"]["tools"]) == 6
    assert len(client.calls[1]["toolConfig"]["tools"]) == 1

def test_workflow_rejects_incomplete_investigation():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

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

    # No proposal-generation request should follow.
    assert len(client.calls) == 1

def test_workflow_rejects_invalid_action_proposal():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
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

    assert len(client.calls) == 2

def test_workflow_rejects_mismatched_proposal_alert():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def converse(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
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
    assert len(client.calls) == 2
