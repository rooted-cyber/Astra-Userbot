import asyncio
import logging
from typing import Any

from config import config
from utils.database import db
from utils.helpers import get_contact_name, edit_or_reply, safe_task
from utils.state import state
from utils.ui_templates import UI

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

    if not config.ENABLE_PM_PROTECTION:
        return True

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

    chat_id = get_primary(message.chat_id)
    sender_id = get_primary(message.sender) if message.sender else chat_id

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
    warnings = state.state["pm_warnings"].get(sender_id, 0) + 1
    state.state["pm_warnings"][sender_id] = warnings
    # Note: StateManager could be improved to handle this increment and save automatically,
    # but for now we manually call save or just use the transient memory.
    # Actually, state.save() background tasks everything.
    safe_task(db.set("pm_warnings", state.state["pm_warnings"]), log_context="PM_Permit:Sync")

    if warnings > config.PM_WARN_LIMIT:
        await edit_or_reply(
            message, f"{UI.mono('[ BLOCK ]')} Access limit exceeded ({config.PM_WARN_LIMIT}). Profile restricted."
        )
        try:
            # We use the bridge call directly if client doesn't have a high-level block
            await client.bridge.call("blockContact", {"contactId": sender_id})
            logger.warning(f"Blocked user {sender_id} due to PM protection violation.")
        except Exception as e:
            logger.error(f"Failed to block user {sender_id}: {e}")
        return False

    # Issue Warning
    pm_name = await get_contact_name(client, sender_id)
    warning_text = (
        f"{UI.header('PM SECURITY ALERT')}\n"
        f"Identify: {UI.bold(pm_name)}\n"
        f"Notice  : Unauthorized private session detected.\n"
        f"Level   : {UI.mono(f'{warnings}/{config.PM_WARN_LIMIT}')} Warnings\n\n"
        f"{UI.italic('Awaiting owner authorization. Persistent messaging results in automated restriction.')}"
    )
    await edit_or_reply(message, warning_text)
    return False
