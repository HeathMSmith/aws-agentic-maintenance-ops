"""Scripted Bedrock Converse responses for offline demonstrations."""


class OfflineBedrockClient:
    """Simulate Bedrock tool requests without calling AWS."""

    def __init__(self):
        self.calls = []

    def converse(self, **kwargs):
        """Return a scripted response for each Converse invocation."""
        self.calls.append(kwargs)

        if len(self.calls) == 1:
            tool_requests = [
                ("get_equipment_alert", {"alert_id": "ALERT-0001"}),
                ("get_asset_context", {"asset_id": "CONV-MTR-042"}),
                ("get_maintenance_history", {"asset_id": "CONV-MTR-042"}),
                ("get_production_schedule", {"asset_id": "CONV-MTR-042"}),
                ("get_maintenance_window_status", {"asset_id": "CONV-MTR-042"}),
            ]

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
                                tool_requests,
                                start=1,
                            )
                        ],
                    }
                },
            }

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
                                    "Elevated vibration and temperature "
                                    "were detected on conveyor motor "
                                    "CONV-MTR-042. "
                                    "Immediate shutdown is authorized."
                                )
                            }
                        ],
                    }
                },
            }

        if len(self.calls) == 3:
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

        raise RuntimeError(
            "OfflineBedrockClient supports exactly three Converse calls"
        )
