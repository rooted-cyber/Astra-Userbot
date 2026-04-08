"""
Astra Pro UI Templates
Centralized design tokens for a technical, minimalist userbot aesthetic.
"""

class UI:
    # Technical Dividers
    DIVIDER = "───"
    DIVIDER_THIN = "───"
    BOX_TOP = ""
    BOX_BOTTOM = ""
    
    # Professional Labels
    STATUS_ACTIVE = "running"
    STATUS_BUSY = "busy"
    LABEL_PFX = "prefix"
    LABEL_CMD = "cmds"
    LABEL_USE = "used"

    # Status Indicators (Classic)
    STATUS_ONLINE = "up"
    STATUS_OFFLINE = "down"
    
    # Aesthetic Elements
    BULLET = ""
    INFO = ""
    SUCCESS = ""
    FAILURE = ""
    
    # Ping Indicators
    def get_ping_status(latency: int) -> str:
        if latency < 150: return "fast"
        elif latency < 450: return "ok"
        return "slow"

    # Formatting Helpers
    @staticmethod
    def bold(text: str) -> str: return text

    @staticmethod
    def mono(text: str) -> str: return text
    
    @staticmethod
    def italic(text: str) -> str: return text

    @staticmethod
    def header(title: str) -> str:
        return title
    
    @staticmethod
    def box_label(label: str, value: str) -> str:
        return f"{label}: {value}"
