"""Tool definitions exposed to Amazon Bedrock Converse API."""

EQUIPMENT_ALERT_TOOL = {
    "toolSpec": {
        "name": "get_equipment_alert",
        "description": (
            "Retrieve an equipment alert by its alert ID. "
            "Returns the alert details, including the affected asset, "
            "severity, observations, and baseline measurements."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": (
                            "Unique identifier of the equipment alert, "
                            "for example ALERT-0001."
                        ),
                    }
                },
                "required": ["alert_id"],
                "additionalProperties": False,
            }
        },
    }
}

ASSET_CONTEXT_TOOL = {
    "toolSpec": {
        "name": "get_asset_context",
        "description": (
            "Retrieve equipment asset metadata by asset ID. "
            "Returns information about the asset, including its name, "
            "type, location, operational status, and criticality. "
            "Use this tool when investigating an alert to understand "
            "the affected equipment and its operational importance."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": "string",
                        "description": (
                            "Unique identifier of the equipment asset, "
                            "for example CONV-MTR-042."
                        ),
                    }
                },
                "required": ["asset_id"],
                "additionalProperties": False,
            }
        },
    }
}

MAINTENANCE_HISTORY_TOOL = {
    "toolSpec": {
        "name": "get_maintenance_history",
        "description": (
            "Retrieve historical maintenance records for an equipment asset. "
            "Returns maintenance activities, dates, findings, corrective "
            "actions, and outcomes, ordered from newest to oldest. "
            "Use this tool when investigating equipment alerts to identify "
            "previous repairs, recurring problems, or relevant service history. "
            "Historical findings do not establish the cause of a current alert."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": "string",
                        "description": (
                            "Unique identifier of the equipment asset, "
                            "for example CONV-MTR-042."
                        ),
                    }
                },
                "required": ["asset_id"],
                "additionalProperties": False,
            }
        },
    }
}

PRODUCTION_SCHEDULE_TOOL = {
    "toolSpec": {
        "name": "get_production_schedule",
        "description": (
            "Retrieve the production schedule associated with an equipment asset. "
            "Returns the production line identifier, name, operational status, "
            "and scheduled activities in chronological order. "
            "Use this tool during equipment investigations to understand "
            "production commitments and planned maintenance windows. "
            "Scheduled activities do not authorize maintenance or shutdown actions."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": "string",
                        "description": (
                            "Unique identifier of the equipment asset, "
                            "for example CONV-MTR-042."
                        ),
                    }
                },
                "required": ["asset_id"],
                "additionalProperties": False,
            }
        },
    }
}

MAINTENANCE_WINDOW_STATUS_TOOL = {
    "toolSpec": {
        "name": "get_maintenance_window_status",
        "description": (
            "Calculate maintenance-window availability for an equipment asset "
            "using a reference timestamp supplied by the application. "
            "Returns the reference timestamp, availability, and details of "
            "the next eligible maintenance window when one exists. "
            "Use this tool instead of independently calculating whether "
            "a scheduled maintenance window is currently available. "
            "Availability does not authorize maintenance or shutdown actions."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": "string",
                        "description": (
                            "Unique identifier of the equipment asset, "
                            "for example CONV-MTR-042."
                        ),
                    }
                },
                "required": ["asset_id"],
                "additionalProperties": False,
            }
        },
    }
}

MAINTENANCE_ACTION_EVALUATION_TOOL = {
    "toolSpec": {
        "name": "evaluate_proposed_maintenance_action",
        "description": (
            "Evaluate a proposed maintenance action against deterministic "
            "incident evidence and operational policy. Returns permitted, "
            "requires_approval, or rejected. This tool only evaluates "
            "actions; it does not approve, schedule, or execute them."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "Identifier of the equipment alert.",
                    },
                    "action": {
                        "type": "string",
                        "description": (
                            "Proposed action to evaluate against policy."
                        ),
                        "enum": [
                            "continue_monitoring",
                            "request_expert_review",
                            "create_maintenance_work_order",
                            "request_equipment_shutdown",
                        ],
                    },
                },
                "required": ["alert_id", "action"],
                "additionalProperties": False,
            }
        },
    }
}

TOOL_CONFIG = {
    "tools": [
        EQUIPMENT_ALERT_TOOL,
        ASSET_CONTEXT_TOOL,
        MAINTENANCE_HISTORY_TOOL,
        PRODUCTION_SCHEDULE_TOOL,
        MAINTENANCE_WINDOW_STATUS_TOOL,
    ]
}
