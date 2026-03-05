"""
Astra Error Reporter
--------------------
Centralized error reporting system with auto-created WhatsApp group.
All system notifications (errors, alerts, boot messages) are sent to
the group first, falling back to owner DM only if group delivery fails.
"""

import asyncio
import logging
import platform
import sys
import time
import traceback
from typing import Optional

from utils.database import db

logger = logging.getLogger("Astra.ErrorReporter")

# Rate limiter to prevent error spam loops
_error_timestamps = []
_MAX_ERRORS_PER_MIN = 5


class ErrorReporter:
    """Singleton error reporter with auto-group creation."""

    _group_id: Optional[str] = None
    _init_lock = asyncio.Lock() if hasattr(asyncio, "Lock") else None
    _initialized = False

    @classmethod
    async def initialize(cls, client):
        """
        Called on bot startup. Creates the error log group if it doesn't
        exist in DB yet. Skips entirely if group ID is already stored.
        """
        if cls._initialized:
            return

        # Check DB first — skip creation if we already have a group
        stored = await db.get("error_log_group_id")
        if stored:
            cls._group_id = stored
            cls._initialized = True
            logger.info(f"Error log group loaded from DB: {stored}")
            return

        # No group in DB — create one
        try:
            me = await client.get_me()
            my_jid = me.id.serialized if hasattr(me.id, "serialized") else str(me.id)

            gid = await client.group.create("「Astra」Error Logs", [my_jid])

            if gid:
                if hasattr(gid, "serialized"):
                    gid = gid.serialized
                gid = str(gid)

                cls._group_id = gid
                await db.set("error_log_group_id", gid)

                try:
                    await client.group.set_description(
                        gid,
                        "🤖 Astra Userbot — Automated Error & System Logs\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "This group was auto-created by Astra.\n"
                        "All errors and system alerts are logged here.\n\n"
                        "⚠️ Do not delete this group."
                    )
                except:
                    pass

                logger.info(f"Auto-created error log group: {gid}")
        except Exception as e:
            logger.warning(f"Failed to create error log group: {e}")

        cls._initialized = True

    @classmethod
    async def _ensure_group(cls, client) -> Optional[str]:
        """Get or create the error log group. Cached after first call."""
        if cls._group_id:
            return cls._group_id

        # If initialize wasn't called yet, do it now
        if not cls._initialized:
            await cls.initialize(client)

        return cls._group_id

    @classmethod
    async def _send_to_group(cls, client, text: str) -> bool:
        """Try sending to the error group. Returns True on success."""
        gid = await cls._ensure_group(client)
        if not gid:
            return False
        try:
            await client.chat.send_message(gid, text)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to error group: {e}")
            return False

    @classmethod
    async def _send_to_owner(cls, client, text: str) -> bool:
        """Fallback: send to owner DM."""
        try:
            from config import config
            owner_ids = getattr(client, "owner_ids", [])
            if not owner_ids and config.OWNER_ID:
                owner_ids = [config.OWNER_ID]
            for oid in owner_ids:
                try:
                    await client.chat.send_message(str(oid), text)
                    return True
                except:
                    continue
        except:
            pass
        return False

    @classmethod
    async def send(cls, client, text: str):
        """
        Send a message to the error group first.
        Falls back to owner DM if group delivery fails.
        """
        if await cls._send_to_group(client, text):
            return True
        return await cls._send_to_owner(client, text)

    @classmethod
    async def report(cls, client, message, exc: Exception, context: str = "Command Failure"):
        """
        Full error report: sends rich diagnostics to group/DM
        and clean feedback to the user.
        """
        from utils.media_exceptions import MediaException
        from utils.helpers import smart_reply

        # Rate limiting
        global _error_timestamps
        now = time.time()
        _error_timestamps = [t for t in _error_timestamps if now - t < 60]
        if len(_error_timestamps) >= _MAX_ERRORS_PER_MIN:
            return
        _error_timestamps.append(now)

        # Build diagnostic report
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        chat_info = ""
        try:
            cid = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
            chat_info = f"*Chat:* `{cid}`\n"
        except:
            pass

        cmd_text = ""
        try:
            cmd_text = f"*Command:* `{(message.body or '')[:80]}`\n"
        except:
            pass

        report_text = (
            f"🚨 *Astra System Alert*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Context:* `{context}`\n"
            f"{chat_info}"
            f"{cmd_text}"
            f"*Error:* `{str(exc)[:200]}`\n"
            f"*Time:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"*Python:* `{sys.version.split()[0]}`\n\n"
            f"*Stack Trace:*\n```\n{tb[:1500]}\n```"
        )

        # Send to group (or DM fallback)
        await cls.send(client, report_text)

        # Send clean user-facing feedback
        try:
            if isinstance(exc, MediaException):
                error_text = (
                    f"{exc.icon} *Astra Media Gateway*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ *Error:* {exc.message}\n\n"
                    f"💡 _Tip:_ Ensure the link is valid and publicly accessible."
                )
            else:
                error_text = (
                    f"⚠️ *Astra System Error*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ Something went wrong while processing your request.\n\n"
                    f"👤 *Details:* `{str(exc)[:100]}`\n"
                    f"🛠️ _Report this at: github.com/paman7647/Astra-Userbot/issues_"
                )
            await smart_reply(message, error_text)
        except:
            pass

    @classmethod
    async def notify(cls, client, text: str):
        """
        Send a system notification (boot, shutdown, etc.) to the group.
        Falls back to owner DM.
        """
        await cls.send(client, text)

    @classmethod
    async def boot_message(cls, client, plugin_count: int = 0):
        """Send a boot notification to the error log group."""
        from config import config

        boot_text = (
            f"✅ *Astra Userbot Online*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Version:* `{config.VERSION}`\n"
            f"*Plugins:* `{plugin_count}` loaded\n"
            f"*Python:* `{sys.version.split()[0]}`\n"
            f"*Platform:* `{platform.system()} {platform.release()}`\n"
            f"*Time:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await cls.send(client, boot_text)


# Convenience aliases
error_reporter = ErrorReporter

async def report_error(client, exc, context=""):
    """Legacy compat wrapper."""
    await ErrorReporter.send(client, (
        f"🚨 *Astra System Alert*\n\n"
        f"*Context:* `{context}`\n"
        f"*Error:* `{str(exc)[:200]}`\n\n"
        f"*Stack Trace:*\n```\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:1500]}\n```"
    ))

async def handle_command_error(client, message, exc, context="Command Failure"):
    """Legacy compat wrapper used by individual commands."""
    await ErrorReporter.report(client, message, exc, context=context)
