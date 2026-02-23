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
        
    status_msg = await smart_reply(message, f"📸 **Capturing screenshot of:** `{url}`...")

    try:
        # Using a reliable public screenshot service
        # thum.io is fast and free for basic usage
        ss_url = f"https://image.thum.io/get/width/1200/crop/800/noAnimate/{url}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(ss_url, timeout=20) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    b64_data = base64.b64encode(img_data).decode('utf-8')
                    
                    media = {
                        "mimetype": "image/jpeg",
                        "data": b64_data,
                        "filename": "screenshot.jpg"
                    }
                    await client.send_media(message.chat_id, media, caption=f"📸 **Screenshot:** {url}")
                    await status_msg.delete()
                    return
                
        await status_msg.edit("⚠️ Failed to capture screenshot. Make sure the URL is valid.")

    except Exception as e:
        await status_msg.edit(f"❌ **Screenshot Error:** {str(e)}")

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

        status_msg = await smart_reply(message, f"🗑️ **Purging {count} messages...**")

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
        
        await status_msg.edit(f"✅ Successfully purged **{deleted_count}** messages.")
        await asyncio.sleep(3)
        await status_msg.delete()

    except Exception as e:
        await smart_reply(message, f"❌ **Purge Error:** {str(e)}")
