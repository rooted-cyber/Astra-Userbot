import base64
import os
import platform
import sys
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

    # Build Pro Report
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

    # Image Handling
    img_source = config.alive_img
    b64 = None
    mimetype = "image/png"

    async def fetch_image(source: str):
        nonlocal b64, mimetype
        if not source: return False
        is_url = source.startswith(("http://", "https://"))
        try:
            if is_url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(source, timeout=10) as resp:
                        if resp.status == 200:
                            b64 = base64.b64encode(await resp.read()).decode()
                            mimetype = resp.headers.get("Content-Type", "image/png")
                            return True
            elif os.path.exists(source):
                with open(source, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    mimetype = "image/jpeg" if source.lower().endswith((".jpg", ".jpeg")) else "image/png"
                    return True
        except: pass
        return False

    success = await fetch_image(img_source)
    if not success and img_source != os.path.join(config.BASE_DIR, "utils", "ub.png"):
        await fetch_image(os.path.join(config.BASE_DIR, "utils", "ub.png"))

    # Determine reply target
    reply_id = message.quoted_message_id if message.has_quoted_msg else message.id

    if b64:
        await client.send_photo(
            message.chat_id,
            {"mimetype": mimetype, "data": b64},
            caption=alive_report,
            reply_to=reply_id,
        )
    else:
        await client.send_message(message.chat_id, alive_report, reply_to=reply_id)

    # Clean up trigger if possible
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
    
    if message.has_quoted_msg and getattr(message.quoted, 'is_media', False):
        status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Downloading image...")
        temp_path = f"/tmp/alive_{int(time.time())}.jpg"
        downloaded = await message.quoted.download() # the framework saves it automatically or requires explicit path? We used download(temp_in) in audio_tools
        if not downloaded:
             downloaded = await message.quoted.download(temp_path)
             if downloaded:
                # Rename to a permanent path in data folder to avoid clearing /tmp
                perm_path = os.path.join(config.BASE_DIR, "utils", f"custom_alive_{int(time.time())}.jpg")
                os.rename(downloaded, perm_path)
                state.set_config("ALIVE_IMG", perm_path)
                return await status_msg.edit(f"{UI.mono('[ OK ]')} Alive image updated to attached media.")
        return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Failed to download media.")
        
    if args:
        url = args[0]
        if url.startswith(("http://", "https://")):
            state.set_config("ALIVE_IMG", url)
            return await edit_or_reply(message, f"{UI.mono('[ OK ]')} Alive image updated to URL.")
            
    await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Please reply to an image or provide a valid URL.")
