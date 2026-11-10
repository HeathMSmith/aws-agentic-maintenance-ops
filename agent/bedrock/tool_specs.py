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


TOOL_CONFIG = {
    "tools": [
        EQUIPMENT_ALERT_TOOL,
    ]
}
