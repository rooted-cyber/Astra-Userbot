"""
some utility tools for the bot
mostly media stuff and some cleanup helpers
"""

import asyncio
import os
import re
import tempfile
import shutil
import time
from typing import Optional

from astra.types import Message

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U0001F1E6-\U0001F1FF"
    "\u2600-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def sanitize_outgoing_text(text: str) -> str:
    """No-op sanitizer: return text unchanged."""
    return text


def safe_task(coro_or_future, log_context: str = "task"):
    """runs stuff in background without crashing things"""
    import logging
    logger = logging.getLogger("Astra.SafeTask")

    async def wrapper():
        try:
            if asyncio.iscoroutine(coro_or_future):
                await coro_or_future
            else:
                await asyncio.wrap_future(coro_or_future)
        except Exception as e:
            logger.error(f"[{log_context}] task failed: {e}")

    return asyncio.ensure_future(wrapper())


async def check_binary(name: str) -> bool:
    """checks if some tool exists in system"""
    return shutil.which(name) is not None


async def get_media_message(message: Message) -> Optional[Message]:
    """gets media from message or reply"""
    if message.is_media:
        return message
    if message.has_quoted_msg:
        quoted = message.quoted
        if quoted and quoted.is_media:
            return quoted
    return None


async def get_media_title(url: str) -> str:
    """
    Attempts to retrieve a human-readable title for a media URL using yt-dlp.
    Falls back to a generic title if retrieval fails.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--get-title",
            "--no-warnings",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        # Silently fail as this is often a non-critical metadata fetch
        pass
    return "Media Content"


# Operational Support Classes
# ---------------------------


class RateLimiter:
    """
    Implements a sliding window rate limiting algorithm.
    Prevents command spam by tracking user-specific execution timestamps.
    """

    def __init__(self, limit: int = 5, window: int = 60):
        self.limit = limit
        self.window = window
        self.records = {}

    def check(self, user_id: str) -> bool:
        """
        Validates if a user is within the allowed rate limit.
        Returns True if allowed, False if throttled.
        """
        now = time.time()

        if user_id not in self.records:
            self.records[user_id] = []

        # Purge timestamps outside the current window
        self.records[user_id] = [t for t in self.records[user_id] if now - t < self.window]

        if len(self.records[user_id]) >= self.limit:
            return False

        self.records[user_id].append(now)
        return True


async def edit_or_reply(message: Message, content: str, **kwargs):
    """
    Edits the triggering message if sent by us, otherwise replies.
    Falls back to a plain send if both edit and reply fail.
    Handles 'Cannot edit message' errors by immediately falling back to reply.
    """
    try:
        # Check if the message is from us and is potentially editable (not too old, not deleted)
        if message.from_me:
            try:
                # We add a small delay to avoid race conditions with bridge processing
                await asyncio.sleep(0.5)
                await message.edit(content)
                return message
            except Exception as e:
                # If editing fails (e.g., Cannot edit message error), we move on to reply
                if "Cannot edit message" in str(e) or "editMessage" in str(e):
                    pass # Handled by the next try block
                else:
                    raise e
    except Exception:
        pass

    try:
        return await message.reply(content, **kwargs)
    except Exception:
        pass

    # Last resort: just send to the chat directly
    try:
        return await message._client.send_message(message.chat_id, content, **kwargs)
    except Exception:
        return None


# Keep backward compat alias
edit_or_reply = edit_or_reply


async def safe_edit(message: Message, content: str, **kwargs):
    """
    A robust version of edit() that automatically falls back to
    edit_or_reply() or message.reply() if editing is not possible.
    Includes built-in protection against common WhatsApp edit restrictions.
    """
    try:
        # If edit is possible (it's from me), attempt it
        if message.from_me:
            await asyncio.sleep(0.5)
            return await message.edit(content, **kwargs)
        else:
            # If not from me, we must reply
            return await edit_or_reply(message, content, **kwargs)
    except Exception:
        # Global fallback for any failure (message deleted, too old, etc.)
        return await edit_or_reply(message, content, **kwargs)


# Error reporting is now handled by the centralized ErrorReporter module.
# It auto-creates a WhatsApp group for logs, falling back to owner DM.
# from utils.error_reporter import report_error, handle_command_error, ErrorReporter (unused here, triggers circularity)


async def get_contact_name(client, jid: str) -> str:
    """
    Priority-based name resolution for any JID.
    Priority: Pushname > Contact Name > Formatted Number > Short JID
    """
    try:
        from astra.types import JID

        jid_obj = JID.parse(jid) if isinstance(jid, str) else jid

        # Check if it's "Me" (LID or User ID matches)
        me = await client.get_me()
        if jid_obj.primary == me.id.primary:
            return "Me"

        clean_jid = jid_obj.primary
        contact = await client.get_contact(clean_jid)

        # Priority Logic
        if contact.push_name:
            return contact.push_name
        if contact.name:
            return contact.name

        # Fallback to number or JID
        user_part = clean_jid.split("@")[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]
    except Exception:
        # Hard fallback
        user_part = str(jid).split("@")[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]


# Exported Singletons
# ------------------
rate_limiter = RateLimiter()


async def send_bytes_media(
    client,
    chat_id,
    data: bytes,
    *,
    filename: str,
    mode: str = "file",
    caption: Optional[str] = None,
    reply_to=None,
    document: bool = False,
):
    """
    Sends in-memory bytes by first writing to a temp file.
    Astra's media methods expect a path/URL, not dict/bytes payloads.
    """
    suffix = os.path.splitext(filename)[1] or ".bin"
    temp_file = tempfile.NamedTemporaryFile(prefix="astra_", suffix=suffix, delete=False)
    temp_path = temp_file.name

    try:
        temp_file.write(data)
        temp_file.flush()
        temp_file.close()

        kwargs = {}
        if caption is not None:
            kwargs["caption"] = caption
        if reply_to is not None:
            kwargs["reply_to"] = reply_to

        if mode == "photo":
            return await client.send_photo(chat_id, temp_path, **kwargs)
        if mode == "document":
            return await client.send_document(chat_id, temp_path, **kwargs)
        return await client.send_file(chat_id, temp_path, document=document, **kwargs)
    finally:
        try:
            if not temp_file.closed:
                temp_file.close()
        except Exception:
            pass
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
