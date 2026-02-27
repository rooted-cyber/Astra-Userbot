# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
import base64
import asyncio
from . import *

@astra_command(
    name="ss",
    description="Take a screenshot of a website.",
    category="Core Tools",
    aliases=["screenshot", "webshot"],
    usage="<url> (e.g. .ss google.com)",
    is_public=True
)
async def ss_handler(client: Client, message: Message):
    """Website screenshot plugin."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.ss <url>`")

    url = args[0]
    if not url.startswith('http'):
        url = 'https://' + url
        
    status_msg = await smart_reply(message, f"📸 **Astra Web Capture**\n━━━━━━━━━━━━━━━━━━━━\n🌐 **Target:** `{url}`...")

    try:
        # Fallback Chain for maximum reliability
        # 1. PageShot (Modern, High Accuracy)
        # 2. WordPress Mshots (Stable Fallback)
        # 3. Thum.io (Speed Fallback)
        providers = [
            f"https://pageshot.site/api/render?url={url}&width=1280&height=720&format=jpeg",
            f"https://s.wordpress.com/mshots/v1/{url}?w=1280&h=720",
            f"https://image.thum.io/get/width/1280/crop/720/noAnimate/{url}"
        ]
        
        provider_names = ["PageShot", "WordPress", "Thum.io"]
        img_data = None
        
        async with aiohttp.ClientSession() as session:
            for i, prov_url in enumerate(providers):
                try:
                    name = provider_names[i]
                    logger.debug(f"📸 Trying {name}...")
                    await status_msg.edit(f"📸 **Astra Web Capture**\n━━━━━━━━━━━━━━━━━━━━\n🌐 **Target:** `{url}`\n⚙️ **Engine:** `{name}`...")
                    
                    async with session.get(prov_url, timeout=25) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            # Validation: Check if it's a real image and not a tiny placeholder/error
                            if len(data) > 5000: # Usually > 5KB for a real screenshot
                                img_data = data
                                break
                            else:
                                logger.debug(f"{name} returned suspiciously small data ({len(data)} bytes)")
                except Exception as prov_err:
                    logger.debug(f"Provider {provider_names[i]} failed: {prov_err}")
                    continue

        if img_data:
            b64_data = base64.b64encode(img_data).decode('utf-8')
            media = {
                "mimetype": "image/jpeg",
                "data": b64_data,
                "filename": "screenshot.jpg"
            }
            await client.send_media(message.chat_id, media, caption=f"📸 **Screenshot:** {url}")
            return await status_msg.delete()
        
        await status_msg.edit("⚠️ **Astra Web Capture:** All capture engines failed. The site might be heavily protected or offline.")

    except Exception as e:
        await status_msg.edit(f"❌ **System Error:** {str(e)}")

@astra_command(
    name="purge",
    description="Delete multiple messages from the current chat.",
    category="Group Admin",
    aliases=["del", "purgemsg"],
    usage="[count] (reply to a message to start purging from there)",
    owner_only=True
)
async def purge_handler(client: Client, message: Message):
    """Bulk message deletion plugin."""
    try:
        if not message.has_quoted_msg:
            return await smart_reply(message, "🗑️ Reply to a message to start purging from there.")

        args = extract_args(message)
        count = int(args[0]) if args and args[0].isdigit() else 10
        count = min(count, 100) # Limit to 100 for safety

        status_msg = await smart_reply(message, f"🗑️ **Astra Purge Utility**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Deleting {count} messages...*")

        # Fetch messages after the quoted one
        # Note: purged messages must be the bot's own or if the bot is admin
        # On WhatsApp, you can usually only delete your own messages for everyone
        # or others' if you are admin.
        
        messages = await client.chat.fetch_messages(
            message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id),
            limit=count,
            message_id=message.quoted.id,
            direction="after"
        )

        to_delete = [message.quoted.id] + [msg.id for msg in messages]
        
        # WhatsApp Web Bridge usually has a bulk delete or we loop
        # For safety and compatibility with current bridge patterns:
        deleted_count = 0
        for msg_id in to_delete:
            try:
                # We try to use a generic delete if available on client
                await client.chat.delete_messages(message.chat_id, [msg_id])
                deleted_count += 1
            except:
                pass
        
        await status_msg.edit(f"✅ **Astra Purge Utility**\n━━━━━━━━━━━━━━━━━━━━\n🗑️ *Successfully purged* **{deleted_count}** *messages.*")
        await asyncio.sleep(3)
        await status_msg.delete()

    except Exception as e:
        await smart_reply(message, f"❌ **Purge Error:** {str(e)}")
