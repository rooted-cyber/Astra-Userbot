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
    category="System & Bot",
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
        
        # Determine if img_source is a URL or local path
        is_url = img_source.startswith(("http://", "https://"))
        
        if is_url or os.path.exists(img_source):
            try:
                b64 = None
                mimetype = "image/png"
                
                if is_url:
                    # Download remote image
                    import requests
                    response = requests.get(img_source, timeout=10)
                    if response.status_code == 200:
                        b64 = base64.b64encode(response.content).decode()
                        mimetype = response.headers.get("Content-Type", "image/png")
                else:
                    # Read local file
                    with open(img_source, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        if img_source.endswith(".jpg") or img_source.endswith(".jpeg"):
                            mimetype = "image/jpeg"

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
            except Exception as e:
                logger.error(f"Failed to process alive image: {e}")

        # Transition high-latency msg to final report
        await status_msg.edit(alive_report)

    except Exception as e:
        await smart_reply(message, f"❌ Alive Error: {str(e)}")
        await report_error(client, e, context="alive status failure")
