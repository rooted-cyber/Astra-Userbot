# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import logging
from typing import List
from dotenv import load_dotenv

# Define base directory for relative path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file from the project root
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger("Astra.Config")

class Config:
    """Bot config container"""
    
    # Versioning
    VERSION = "0.0.3b2"
    VERSION_NAME = "Beta 2 (v0.0.3)"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Bot Identity
    @property
    def BOT_NAME(self) -> str:
        from utils.state import state
        return state.get_config("BOT_NAME") or os.getenv('BOT_NAME', 'Astra Userbot')
    
    # OWNER_ID is critical for security and administrative commands.
    # We resolve it from either OWNER_WHATSAPP_ID, BOT_OWNER_ID, or PHONE_NUMBER.
    OWNER_ID = os.getenv('OWNER_WHATSAPP_ID') or os.getenv('BOT_OWNER_ID') or os.getenv('PHONE_NUMBER')
    @property
    def OWNER_NAME(self) -> str:
        from utils.state import state
        return state.get_config("OWNER_NAME") or os.getenv('OWNER_NAME', 'Aman Kumar Pandey')
    
    _DEFAULT_PREFIX = os.getenv('COMMAND_PREFIX', '.')

    @property
    def PREFIX(self) -> str:
        from utils.state import state
        return state.get_prefix()

    @property
    def PREFIXES(self) -> List[str]:
        p = self.PREFIX
        return [p, '!', '/'] if p not in ['!', '/'] else ['.', '!', '/']

    # Feature Flags
    @property
    def ENABLE_AI(self) -> bool:
        from utils.state import state
        val = state.get_config("ENABLE_AI")
        if val is not None: return bool(val)
        return os.getenv('ENABLE_AI', 'true').lower() == 'true'

    @property
    def ENABLE_YOUTUBE(self) -> bool:
        from utils.state import state
        val = state.get_config("ENABLE_YOUTUBE")
        if val is not None: return bool(val)
        return os.getenv('ENABLE_YOUTUBE', 'true').lower() == 'true'

    @property
    def ENABLE_INSTAGRAM(self) -> bool:
        from utils.state import state
        val = state.get_config("ENABLE_INSTAGRAM")
        if val is not None: return bool(val)
        return os.getenv('ENABLE_INSTAGRAM', 'true').lower() == 'true'

    @property
    def ENABLE_PM_PROTECTION(self) -> bool:
        from utils.state import state
        val = state.get_config("ENABLE_PM_PROTECTION")
        if val is not None: return bool(val)
        return os.getenv('ENABLE_PM_PROTECTION', 'false').lower() == 'true'

    @property
    def PM_WARN_LIMIT(self) -> int:
        from utils.state import state
        val = state.get_config("PM_WARN_LIMIT")
        if val is not None: return int(val)
        return int(os.getenv('PM_WARN_LIMIT', '5'))

    # Prefix handling: toggle multiple prefix support
    @property
    def ALLOW_MULTI_PREFIX(self) -> bool:
        from utils.state import state
        val = state.get_config("ALLOW_MULTI_PREFIX")
        if val is not None: return bool(val)
        return os.getenv('ALLOW_MULTI_PREFIX', 'false').lower() == 'true'
    
    # Persistence & Synchronization
    # -----------------------------
    MONGO_URI = os.getenv('MONGO_URI')
    _sqlite_path = os.getenv('SQLITE_PATH', 'bot_state.db')
    
    # Resolve SQLite path relative to the script directory if it's not absolute
    SQLITE_PATH = _sqlite_path if os.path.isabs(_sqlite_path) else os.path.join(BASE_DIR, _sqlite_path)
    
    # Interval for background database sync (in seconds)
    DATABASE_SYNC_INTERVAL = int(os.getenv('DATABASE_SYNC_INTERVAL', '300'))

    # Third-party API Orchestration
    # -----------------------------
    @property
    def GEMINI_API_KEY(self) -> str:
        from utils.state import state
        return state.get_config("GEMINI_API_KEY") or os.getenv('GEMINI_API_KEY')

    @property
    def NEWS_API_KEY(self) -> str:
        from utils.state import state
        return state.get_config("NEWS_GEMINI_API_KEY") or os.getenv('NEWS_GEMINI_API_KEY')

    # Media Processing & Binary Paths
    # -------------------------------
    @property
    def FFMPEG_PATH(self) -> str:
        from utils.state import state
        return state.get_config("FFMPEG_PATH") or os.getenv('FFMPEG_PATH', 'ffmpeg')
    
    # YouTube session handling
    YOUTUBE_COOKIES_FILE = os.getenv('YOUTUBE_COOKIES_FILE')
    YOUTUBE_COOKIES_FROM_BROWSER = os.getenv('YOUTUBE_COOKIES_FROM_BROWSER')

    # Resource Constraints & Timeouts
    # -------------------------------
    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        from utils.state import state
        val = state.get_config("MAX_FILE_SIZE_MB")
        if val is not None: return int(val)
        return int(os.getenv('MAX_FILE_SIZE_MB', '2048'))

    @property
    def REQUEST_TIMEOUT(self) -> int:
        from utils.state import state
        val = state.get_config("REQUEST_TIMEOUT")
        if val is not None: return int(val)
        return int(os.getenv('REQUEST_TIMEOUT', '30000'))

    # Getter methods for Dynamic Configs (v6.0)
    # ----------------------------------------
    @property
    def alive_img(self) -> str:
        """Dynamically resolves the image for .alive command."""
        from utils.state import state
        return state.get_config("ALIVE_IMG") or os.path.join(BASE_DIR, "utils", "ub.png")

    @property
    def bot_name(self) -> str:
        return self.BOT_NAME

    def __init__(self):
        self._validate()

    def _validate(self):
        """Perform basic integrity checks on the loaded configuration."""
        if not self.OWNER_ID:
            logger.warning("OWNER_ID is not configured. Administrative commands will be inaccessible.")

# Singleton instance for global access
config = Config()
