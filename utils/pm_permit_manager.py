import logging
from typing import Any

from config import config
from utils.helpers import get_contact_name, edit_or_reply
from utils.state import state

from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.PMPermit")


async def enforce_pm_protection(client: Client, message: Message):
    """
    Enforces PM protection by checking if the sender is permitted.
    If not, it issues warnings or blocks depending on the configuration.
    """
    # Safeguard: Wait for state to be ready to avoid using default values
    # if the bot just started and messages are flowing in.
    if not state.initialized:
        await state.initialize()

    protection_enabled = bool(
        state.get_config("ENABLE_PM_PROTECTION", getattr(config, "ENABLE_PM_PROTECTION", True))
    )
    if not protection_enabled:
        return True

    warn_limit_raw = state.get_config("PM_WARN_LIMIT", getattr(config, "PM_WARN_LIMIT", 3))
    try:
        warn_limit = max(1, int(warn_limit_raw))
    except Exception:
        warn_limit = 3

    # 1. Resolve IDs safely (handles both JID objects and strings)
    # We always use the primary JID (stripping device stickers like :4) for logic checks
    def get_primary(jid: Any) -> str:
        """Provides a normalized ID without device markers."""
        if not jid:
            return ""
        s = jid.serialized if hasattr(jid, "serialized") else str(jid)
        if "@" not in s:
            return s
        parts = s.split("@")
        user = parts[0].split(":")[0]
        return f"{user}@{parts[1]}"

    chat_id = state._normalize_contact_id(get_primary(message.chat_id))
    sender_raw = message.sender if getattr(message, "sender", None) else getattr(message, "author", None)
    sender_id = state._normalize_contact_id(get_primary(sender_raw) if sender_raw else chat_id)

    # 2. Skip if not a private message (@c.us or @lid)
    is_private = chat_id.endswith("@c.us") or chat_id.endswith("@lid")
    if not is_private:
        return True

    # 3. Skip if security exclusions apply
    # Exclude Bot Owner
    sender_num = sender_id.split("@")[0]
    if str(config.OWNER_ID) == sender_num:
        return True

    # Exclude From Me (Self Account / My own replies)
    if message.from_me:
        return True

    # Exclude Sudo Users
    if state.is_sudo(sender_id):
        return True

    # Exclude Whitelisted/Permitted Users
    if state.is_permitted(sender_id):
        return True

    # 3. Handle Violation
    logger.info(f"PM Protection triggered for {sender_id}")

    # Increment Warning Count
    warnings = state.increment_pm_warning(sender_id)

    if warnings > warn_limit:
        await edit_or_reply(
            message,
            f"PM warning limit exceeded ({warn_limit}). You have been blocked.",
        )
        try:
            if hasattr(client, "bridge") and client.bridge:
                await client.bridge.call("blockContact", {"contactId": sender_id})
            elif hasattr(client, "contact") and hasattr(client.contact, "block"):
                await client.contact.block(sender_id)
            logger.warning(f"Blocked user {sender_id} due to PM protection violation.")
        except Exception as e:
            logger.error(f"Failed to block user {sender_id}: {e}")
        return False

    # Issue Warning
    pm_name = await get_contact_name(client, sender_id)
    warning_text = (
        "PM protection is enabled.\n"
        f"User: {pm_name}\n"
        f"Warning: {warnings}/{warn_limit}\n\n"
        "Wait for owner approval. Repeated messages will trigger auto-block."
    )
    await edit_or_reply(message, warning_text)
    return False
