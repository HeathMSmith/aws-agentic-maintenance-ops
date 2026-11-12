"""Build instructions for evidence-based equipment investigations."""


def build_investigation_prompt(alert_id: str) -> str:
    """Describe the required evidence collection and investigation scope."""

    return (
        f"Investigate equipment alert {alert_id}.\n\n"
        "First, retrieve the equipment alert using get_equipment_alert. "
        "Use the asset_id returned by that tool for all subsequent "
        "asset-related evidence requests.\n\n"
        "Retrieve and review evidence using these tools:\n"
        "- get_asset_context\n"
        "- get_maintenance_history\n"
        "- get_production_schedule\n"
        "- get_maintenance_window_status\n\n"
        "Do not complete the investigation until all five evidence "
        "tools, including get_equipment_alert, have returned successfully.\n\n"
        "Summarize the observed equipment condition, relevant maintenance "
        "history, production impact, and maintenance-window availability. "
        "Distinguish observations from possible causes.\n\n"
        "Do not claim that any maintenance or equipment shutdown action "
        "has been authorized. Your role is to investigate and report "
        "evidence, not approve operational actions."
    )
