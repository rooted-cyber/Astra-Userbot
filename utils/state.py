"""
Centralized State Management
----------------------------
Orchestrates the persistent and ephemeral state of the userbot.
Synchronizes local memory cache with the SQLite backend.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from .database import db

logger = logging.getLogger("Astra.State")

# Capture the exact unix timestamp when the process/module started.
# Used to ignore messages sent before the bot was online.
BOOT_TIME = int(time.time())


class StateManager:
    """
    Maintains the runtime state of the userbot.
    Features a local cache for high-speed synchronous reads and
    asynchronous write-through to the database.
    """

    def __init__(self):
        # Local state cache to avoid frequent database I/O for reads.
        self.state: Dict[str, Any] = {
            "afk": {"is_afk": False, "reason": "", "since": 0},
            "pm_permits": [],
            "sudo_users": [],
            "notes": {},
            "pm_warnings": {},
            "group_configs": {},  # gid -> {muted: bool, welcome: str}
            "prefix": None,
            "FULL_DEV": True,  # Infrastructure enabled by default
            "I_DEV": False,  # Privacy filter bypass (Disabled by default)
            "configs": {},  # Dynamic runtime configurations
        }
        self.initialized = False

    async def initialize(self):
        """
        Synchronizes the memory state with the persistent database.
        Must be called during the bot startup sequence.
        """
        if self.initialized:
            return

        await db.initialize()

        # Bulk load managed state keys
        keys = [
            "afk",
            "pm_permits",
            "sudo_users",
            "notes",
            "pm_warnings",
            "group_configs",
            "prefix",
            "I_DEV",
            "FULL_DEV",
            "configs",
        ]
        for key in keys:
            val = await db.get(key)
            if val is not None:
                if key == "configs" and not isinstance(val, dict):
                    val = {}
                self.state[key] = val

        self.initialized = True
        logger.info("StateManager successfully synchronized with persistent store.")

    async def save(self):
        """
        Force-syncs the entire memory state to the database.
        Note: The class handles individual state changes automatically;
        this remains for manual consistency checks.
        """
        tasks = [db.set(key, val) for key, val in self.state.items()]
        if tasks:
            await asyncio.gather(*tasks)

    # --- AFK Module ---

    def set_afk(self, is_afk: bool, reason: str = ""):
        """Toggles the AFK (Away From Keyboard) status."""
        self.state["afk"] = {"is_afk": is_afk, "reason": reason, "since": int(time.time()) if is_afk else 0}
        # Commit to storage in the background
        asyncio.create_task(db.set("afk", self.state["afk"]))

    def get_afk(self) -> Dict[str, Any]:
        """Retrieves current AFK status and metadata."""
        return self.state["afk"]

    # --- Direct Message Security (PM Permit) ---

    def _normalize_contact_id(self, user_id: str) -> str:
        """Normalize private contact IDs for permit and warning keys."""
        return self._normalize_user_id(user_id)

    def is_permitted(self, user_id: str) -> bool:
        """Validates if a specific user is authorized to send direct messages."""
        normalized = self._normalize_contact_id(user_id)
        if not normalized:
            return False

        permits = set(self.state["pm_permits"])
        if normalized in permits:
            return True

        if normalized.endswith("@c.us"):
            return normalized.replace("@c.us", "@s.whatsapp.net") in permits
        if normalized.endswith("@s.whatsapp.net"):
            return normalized.replace("@s.whatsapp.net", "@c.us") in permits
        return False

    def permit_user(self, user_id: str):
        """Adds a user to the whitelist for direct messages."""
        normalized = self._normalize_contact_id(user_id)
        if normalized and normalized not in self.state["pm_permits"]:
            self.state["pm_permits"].append(normalized)
            asyncio.create_task(db.set("pm_permits", self.state["pm_permits"]))

    def deny_user(self, user_id: str):
        """Removes a user from the direct message whitelist."""
        normalized = self._normalize_contact_id(user_id)
        if not normalized:
            return

        variants = {normalized}
        if normalized.endswith("@c.us"):
            variants.add(normalized.replace("@c.us", "@s.whatsapp.net"))
        if normalized.endswith("@s.whatsapp.net"):
            variants.add(normalized.replace("@s.whatsapp.net", "@c.us"))

        original_len = len(self.state["pm_permits"])
        self.state["pm_permits"] = [u for u in self.state["pm_permits"] if u not in variants]
        if len(self.state["pm_permits"]) != original_len:
            asyncio.create_task(db.set("pm_permits", self.state["pm_permits"]))

    def get_permitted_users(self):
        """Returns a copy of PM permitted users."""
        return list(self.state.get("pm_permits", []))

    def get_pm_warning(self, user_id: str) -> int:
        normalized = self._normalize_contact_id(user_id)
        return int(self.state["pm_warnings"].get(normalized, 0)) if normalized else 0

    def increment_pm_warning(self, user_id: str) -> int:
        normalized = self._normalize_contact_id(user_id)
        if not normalized:
            return 0
        count = int(self.state["pm_warnings"].get(normalized, 0)) + 1
        self.state["pm_warnings"][normalized] = count
        asyncio.create_task(db.set("pm_warnings", self.state["pm_warnings"]))
        return count

    def clear_pm_warning(self, user_id: str):
        normalized = self._normalize_contact_id(user_id)
        if normalized and normalized in self.state["pm_warnings"]:
            del self.state["pm_warnings"][normalized]
            asyncio.create_task(db.set("pm_warnings", self.state["pm_warnings"]))

    def clear_all_pm_warnings(self):
        self.state["pm_warnings"] = {}
        asyncio.create_task(db.set("pm_warnings", self.state["pm_warnings"]))

    # --- Administrative Sudo Privileges ---

    @staticmethod
    def _normalize_user_id(user_id: str) -> str:
        """Normalize user IDs/JIDs so sudo checks are consistent across domains/devices."""
        uid = str(user_id or "").strip()
        if not uid:
            return ""

        # Keep full group ids unchanged.
        if uid.endswith("@g.us"):
            return uid

        # Convert @s.whatsapp.net to @c.us and strip device suffixes like 12345:7@c.us
        if "@" in uid:
            local, domain = uid.split("@", 1)
            local = local.split(":", 1)[0]
            domain = "c.us" if domain in ("s.whatsapp.net", "c.us") else domain
            return f"{local}@{domain}"

        # Bare numeric fallback
        return f"{uid}@c.us" if uid.isdigit() else uid

    def is_sudo(self, user_id: str) -> bool:
        """Checks if a user has elevated sudo privileges."""
        normalized = self._normalize_user_id(user_id)
        if not normalized:
            return False

        sudo_set = set(self.state["sudo_users"])
        if normalized in sudo_set:
            return True

        # Backward compatibility for any historical storage variant.
        if normalized.endswith("@c.us"):
            return normalized.replace("@c.us", "@s.whatsapp.net") in sudo_set
        if normalized.endswith("@s.whatsapp.net"):
            return normalized.replace("@s.whatsapp.net", "@c.us") in sudo_set
        return False

    def add_sudo(self, user_id: str):
        """Grants sudo privileges to a user."""
        normalized = self._normalize_user_id(user_id)
        if normalized and normalized not in self.state["sudo_users"]:
            self.state["sudo_users"].append(normalized)
            asyncio.create_task(db.set("sudo_users", self.state["sudo_users"]))

    def remove_sudo(self, user_id: str) -> bool:
        """Revokes sudo privileges from a user. Returns True if removed."""
        normalized = self._normalize_user_id(user_id)
        if not normalized:
            return False

        candidates = {normalized}
        if normalized.endswith("@c.us"):
            candidates.add(normalized.replace("@c.us", "@s.whatsapp.net"))
        if normalized.endswith("@s.whatsapp.net"):
            candidates.add(normalized.replace("@s.whatsapp.net", "@c.us"))

        removed = False
        self.state["sudo_users"] = [u for u in self.state["sudo_users"] if not (u in candidates and (removed := True))]
        if removed:
            asyncio.create_task(db.set("sudo_users", self.state["sudo_users"]))
        return removed

    def get_sudo_users(self):
        """Returns a copy of sudo users list."""
        return list(self.state.get("sudo_users", []))

    # --- Customizable Notes System ---

    def set_note(self, keyword: str, content: str):
        """Saves a snippet of text for quick recall via a keyword."""
        self.state["notes"][keyword.lower()] = content
        asyncio.create_task(db.set("notes", self.state["notes"]))

    def get_note(self, keyword: str) -> Optional[str]:
        """Recalls a previously saved note by its keyword."""
        return self.state["notes"].get(keyword.lower())

    def delete_note(self, keyword: str):
        """Permanently deletes a saved note."""
        if keyword.lower() in self.state["notes"]:
            del self.state["notes"][keyword.lower()]
            asyncio.create_task(db.set("notes", self.state["notes"]))

    # --- Dynamic Interface Routing ---

    def get_prefix(self) -> str:
        """Resolves the current command prefix. Defaults to configuration value."""
        from config import config

        return self.state.get("prefix") or getattr(config, "_DEFAULT_PREFIX", ".")

    def set_prefix(self, prefix: str):
        """Updates the global command prefix for the bot."""
        self.state["prefix"] = prefix
        asyncio.create_task(db.set("prefix", prefix))

    # --- Security & Developer Mode ---

    def is_dev(self) -> bool:
        """Checks if both FULL_DEV and I_DEV are enabled to bypass security filters."""
        return self.state.get("FULL_DEV", False) and self.state.get("I_DEV", False)

    def set_dev_mode(self, enabled: bool):
        """Toggles the internal developer mode (I_DEV)."""
        self.state["I_DEV"] = enabled
        asyncio.create_task(db.set("I_DEV", enabled))

    # --- Dynamic Configuration Management ---

    def set_config(self, key: str, value: Any):
        """Sets a dynamic configuration value in the database."""
        self.state["configs"][key] = value
        asyncio.create_task(db.set("configs", self.state["configs"]))

    def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieves a dynamic configuration value."""
        return self.state["configs"].get(key, default)

    def get_all_configs(self) -> Dict[str, Any]:
        """Returns all dynamic configurations."""
        return self.state["configs"]


# Singleton Export
state = StateManager()
