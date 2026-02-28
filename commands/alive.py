# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import sys
import platform
import base64
import time
from . import *
from config import config

@astra_command(
    name="alive",
    description="Check bot responsiveness and view detailed system status.",
    category="Tools & Utilities",
    aliases=[],
    usage=".alive",
    owner_only=True
)
async def alive_handler(client: Client, message: Message):
    """Renders a real-time professional status report matching high-end userbots."""
    try:
        # 1. Real-time Feel: Initial Status
        status_msg = await smart_reply(message, "⚙️ **Astra Engine:** `Pinging infrastructure...`")
        start_ping = time.time()

        # 2. Collect Metadata
        from utils.state import BOOT_TIME
        uptime_sec = int(time.time() - BOOT_TIME)
        
        def format_uptime(seconds):
            d = seconds // 86400
            h = (seconds % 86400) // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            res = ""
            if d: res += f"{d}d "
            if h: res += f"{h}h "
            if m: res += f"{m}m "
            res += f"{s}s"
            return res.strip()

        # Resolve Engine & Version
        import astra
        engine_ver = getattr(astra, "__version__", "1.0.0")
        db_type = "MongoDB" if config.MONGO_URI else "SQLite"

        # Resolve Owner
        owner_name = config.OWNER_NAME
        try:
            me = await client.get_me()
            owner_name = getattr(me, 'pushname', getattr(me, 'name', owner_name))
        except: pass

        # 3. Build Professional Report
        alive_report = (
            f"💠 **ASTRA USERBOT IS ONLINE** 💠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Owner:** `{owner_name}`\n"
            f"🏷️ **Version:** `{config.VERSION}` ({config.VERSION_NAME})\n"
            f"⚙️ **Engine:** `v{engine_ver}` (Astra)\n"
            f"🐍 **Python:** `v{sys.version.split()[0]}`\n"
            f"🖥️ **OS:** `{platform.system()}`\n"
            f"🗄️ **Database:** `{db_type}`\n"
            f"⏱️ **Uptime:** `{format_uptime(uptime_sec)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 **Repo:** [Astra-Userbot](https://github.com/paman7647/Astra-Userbot)\n"
            f"🔗 **Lib:** [Astra](https://github.com/paman7647/Astra)\n\n"
            f"🚀 *System is optimized and serving with zero latency.*"
        )

        # 4. Handle Media/Text Output
        img_source = config.alive_img
        b64 = None
        mimetype = "image/png"
        
        async def fetch_image(source: str):
            nonlocal b64, mimetype
            is_url = source.startswith(("http://", "https://"))
            try:
                if is_url:
                    import aiohttp
                    async with aiohttp.ClientSession() as img_session:
                        async with img_session.get(source, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                data = await response.read()
                                b64 = base64.b64encode(data).decode()
                                mimetype = response.headers.get("Content-Type", "image/png")
                                return True
                            else:
                                logger.warning(f"Alive Image URL returned {response.status}. Falling back to default.")
                                return False
                elif os.path.exists(source):
                    with open(source, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        if source.endswith(".jpg") or source.endswith(".jpeg"):
                            mimetype = "image/jpeg"
                        return True
            except Exception as e:
                logger.error(f"Failed to process alive image: {e}")
            return False

        # Attempt to fetch custom image
        success = await fetch_image(img_source)
        
        # Fallback to default if custom fails
        if not success and img_source != os.path.join(config.BASE_DIR, "utils", "ub.png"):
            await fetch_image(os.path.join(config.BASE_DIR, "utils", "ub.png"))

        if b64:
            # Delete high-latency pin/edit msg if sending media
            await status_msg.delete()
            
            await client.send_media(
                message.chat_id,
                {"mimetype": mimetype, "data": b64, "filename": "alive.png"},
                caption=alive_report,
                reply_to=message.id
            )
            return

        # Transition high-latency msg to final text-only report if all images fail
        await status_msg.edit(alive_report)

    except Exception as e:
        await smart_reply(message, f"❌ Alive Error: {str(e)}")
        await report_error(client, e, context="alive status failure")
