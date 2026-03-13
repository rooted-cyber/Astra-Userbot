"""
Astra Pro UI Templates
Centralized design tokens for a technical, minimalist userbot aesthetic.
"""

class UI:
    # Technical Dividers
    DIVIDER = "──────────────────────────"
    DIVIDER_THIN = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    BOX_TOP = "╭──────────────────────────"
    BOX_BOTTOM = "╰──────────────────────────"
    
    # Professional Labels
    STATUS_ACTIVE = " ⦗ ACTIVE ⦘ "
    STATUS_BUSY = " ⦗ BUSY... ⦘ "
    LABEL_PFX = " ⧉ PREFIX "
    LABEL_CMD = " ✺ TOTAL "
    LABEL_USE = " ⚡ USAGE "

    # Status Indicators (Classic)
    STATUS_ONLINE = " [ ONLINE ] "
    STATUS_OFFLINE = " [ OFFLINE ] "
    
    # Aesthetic Elements
    BULLET = " ➜ "
    INFO = " ℹ "
    SUCCESS = " ✔ "
    FAILURE = " ✖ "
    
    # Ping Indicators
    def get_ping_status(latency: int) -> str:
        if latency < 150: return "EXCELLENT"
        elif latency < 450: return "STABLE"
        return "AVERAGE"

    # Formatting Helpers
    @staticmethod
    def bold(text: str) -> str: return f"*{text}*"

    @staticmethod
    def mono(text: str) -> str: return f"`{text}`"
    
    @staticmethod
    def italic(text: str) -> str: return f"_{text}_"

    @staticmethod
    def header(title: str) -> str:
        return f"{UI.bold(title)}\n{UI.DIVIDER}"
    
    @staticmethod
    def box_label(label: str, value: str) -> str:
        return f"{UI.bold(label)} : {UI.mono(value)}"
