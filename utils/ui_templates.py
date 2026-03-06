"""
Astra Pro UI Templates
Centralized design tokens for a technical, minimalist userbot aesthetic.
"""

class UI:
    # Dividers
    DIVIDER = "──────────────────────────"
    DIVIDER_THIN = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    
    # Status Indicators
    STATUS_ONLINE = " [ ONLINE ] "
    STATUS_OFFLINE = " [ OFFLINE ] "
    STATUS_BUSY = " [ BUSY ] "
    
    # Aesthetic Elements
    BULLET = " ➜ "
    INFO = " i "
    SUCCESS = " ✓ "
    FAILURE = " ✗ "
    
    # Ping Indicators
    def get_ping_status(latency: int) -> str:
        if latency < 150:
            return "EXCELLENT"
        elif latency < 450:
            return "STABLE"
        return "AVERAGE"

    # Formatting Helpers
    @staticmethod
    def bold(text: str) -> str:
        return f"*{text}*"

    @staticmethod
    def mono(text: str) -> str:
        return f"`{text}`"
    
    @staticmethod
    def italic(text: str) -> str:
        return f"_{text}_"

    @staticmethod
    def header(title: str) -> str:
        return f"{UI.bold(title)}\n{UI.DIVIDER}"
