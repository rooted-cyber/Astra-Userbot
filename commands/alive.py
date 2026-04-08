import os
import platform
import time
from datetime import datetime

from config import config
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="alive",
    description="Check system status and engine integrity.",
    category="Tools & Utilities",
    aliases=[],
    usage=".alive",
    owner_only=True,
)
async def alive_handler(client: Client, message: Message):
    """Renders a minimalist technical status report."""

    from utils.state import BOOT_TIME
    uptime_sec = int(time.time() - BOOT_TIME)

    def format_uptime(seconds):
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{d}d {h}h {m}m {s}s" if d else f"{h}h {m}m {s}s"

    import astra
    engine_ver = getattr(astra, "__version__", "1.0.0")
    db_type = "MongoDB" if config.MONGO_URI else "SQLite"

    # Resolve Owner
    owner_name = config.OWNER_NAME
    try:
        me = await client.get_me()
        owner_name = getattr(me, "pushname", getattr(me, "name", owner_name))
    except:
        pass

    # Build Report
    alive_report = (
        f"{UI.header('SYSTEM INTEGRITY')}\n"
        f"Owner    : {UI.mono(owner_name)}\n"
        f"Version  : {UI.mono(config.VERSION)}\n"
        f"Engine   : {UI.mono(f'v{engine_ver}')}\n"
        f"Database : {UI.mono(db_type)}\n"
        f"Uptime   : {UI.mono(format_uptime(uptime_sec))}\n"
        f"OS       : {UI.mono(platform.system())}\n"
        f"{UI.DIVIDER}\n"
        f"Status   : {UI.mono('[ OPTIMAL ]')}\n"
        f"Service  : {UI.mono('Astra Secure Bridge')}"
    )

    # -------- Image Handling (FIXED) -------- #

    async def resolve_media(source: str):
        """Return a valid file path or URL, else None."""
        if not source:
            return None

        # URL
        if source.startswith(("http://", "https://")):
            return source

        # Local file
        if os.path.exists(source):
            return source

        return None

    # Try main image
    media = await resolve_media(config.alive_img)

    # Fallback image
    if not media:
        fallback = os.path.join(config.BASE_DIR, "utils", "ub.png")
        media = await resolve_media(fallback)

    # Reply target
    reply_id = message.quoted_message_id if message.has_quoted_msg else message.id

    # Send response
    try:
        if media:
            await client.send_photo(
                message.chat_id,
                media,
                caption=alive_report,
                reply_to=reply_id,
            )
        else:
            await client.send_message(
                message.chat_id,
                alive_report,
                reply_to=reply_id,
            )
    except Exception as e:
        # Fallback safety
        await client.send_message(
            message.chat_id,
            f"{alive_report}\n\n[Media Error: {e}]",
            reply_to=reply_id,
        )

    # Cleanup trigger
    try:
        if message.from_me:
            await message.delete()
    except:
        pass


@astra_command(
    name="setalive",
    description="Set a custom alive image via reply or URL.",
    category="Tools & Utilities",
    usage="<reply to image | url>",
    owner_only=True,
)
async def setalive_handler(client: Client, message: Message):
    from utils.state import state
    from utils.plugin_utils import extract_args

    args = extract_args(message)

    # 📸 If replying to an image
    if message.has_quoted_msg and getattr(message.quoted, "is_media", False):
        status_msg = await edit_or_reply(
            message, f"{UI.mono('[ BUSY ]')} Downloading image..."
        )

        try:
            temp_path = await message.quoted.download()

            if not temp_path:
                return await status_msg.edit(
                    f"{UI.mono('[ ERROR ]')} Failed to download media."
                )

            # Save permanently
            perm_path = os.path.join(
                config.BASE_DIR,
                "utils",
                f"custom_alive_{int(time.time())}.jpg",
            )

            os.rename(temp_path, perm_path)
            state.set_config("ALIVE_IMG", perm_path)

            return await status_msg.edit(
                f"{UI.mono('[ OK ]')} Alive image updated."
            )

        except Exception as e:
            return await status_msg.edit(
                f"{UI.mono('[ ERROR ]')} {str(e)}"
            )

    # 🌐 If URL provided
    if args:
        url = args[0]
        if url.startswith(("http://", "https://")):
            state.set_config("ALIVE_IMG", url)
            return await edit_or_reply(
                message, f"{UI.mono('[ OK ]')} Alive image updated to URL."
            )

    # ❌ Invalid usage
    await edit_or_reply(
        message,
        f"{UI.mono('[ ERROR ]')} Reply to an image or provide a valid URL.",
    )
