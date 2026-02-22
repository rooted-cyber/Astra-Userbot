# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Essential Utilities: Paste, Carbon, Quotly
------------------------------------------
A suite of tools for developers and power users.
- Paste: Upload text to pastebin.
- Carbon: Generate beautiful code images.
- Quotly: Create sticker quotes from messages.
"""

import aiohttp
import base64
import time
from utils.helpers import get_contact_name, safe_edit
from . import *

# --- PASTEBIN UTILITY ---
@astra_command(
    name="paste",
    description="Upload text to dpaste.org (Pastebin).",
    category="Astra Essentials",
    aliases=["bin"],
    usage="<text/reply> (reply to a message or provide text)",
    is_public=True
)
async def paste_handler(client: Client, message: Message):
    """
    Uploads text to dpaste.org and returns a viewing link.
    """
    try:
        args_list = extract_args(message)
        content = ""
        
        if message.has_quoted_msg:
            content = message.quoted.body
        elif args_list:
            content = " ".join(args_list)
            
        if not content:
            return await smart_reply(message, " 📋 **Paste Utility**\n\nReply to text or provide arguments.")

        status_msg = await smart_reply(message, " ⏳ *Uploading to dpaste...*")
        
        # Using dpaste.org API (Simple POST, returns URL)
        url = "https://dpaste.org/api/"
        payload = {"content": content, "expiry_days": 7}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status == 200:
                    paste_url = await resp.text()
                    
                    await safe_edit(
                        status_msg,
                        f"🗒️ **Paste Uploaded!**\n\n"
                        f"🔗 **Link:** [View Paste]({paste_url})\n"
                        f"⏳ **Expires:** 7 days"
                    )
                else:
                    await safe_edit(status_msg, " ⚠️ Upload failed. dpaste.org returned error.")

    except Exception as e:
        await report_error(client, e, context='Paste command failure')


# --- CARBON CODE IMAGE ---
@astra_command(
    name="carbon",
    description="Create a beautiful code snippet image.",
    category="Astra Essentials",
    aliases=["code"],
    usage="<text/reply> (reply to code or paste text)",
    is_public=True
)
async def carbon_handler(client: Client, message: Message):
    """
    Uses Carbonara API to generate code images.
    """
    try:
        args_list = extract_args(message)
        code = ""
        
        if message.has_quoted_msg:
            code = message.quoted.body
        elif args_list:
            code = " ".join(args_list)
            
        if not code:
            return await smart_reply(message, " 💻 **Carbon Utility**\n\nReply to code or text.")

        status_msg = await smart_reply(message, " 🎨 *Generating Carbon image...*")
        
        # Carbonara API
        url = "https://carbonara.solopov.dev/api/cook"
        payload = {
            "code": code,
            "backgroundColor": "rgba(171, 184, 195, 1)",
            "theme": "seti"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    media = {
                        "mimetype": "image/jpeg",
                        "data": b64_data,
                        "filename": "carbon.jpg"
                    }
                    await client.send_media(message.chat_id, media, caption="💻 **Code Snippet**")
                    await status_msg.delete()
                else:
                    await safe_edit(status_msg, " ⚠️ Failed to generate image.")

    except Exception as e:
        await report_error(client, e, context='Carbon command failure')


# --- QUOTLY STICKER ---
@astra_command(
    name="quotly",
    description="Create a sticker quote from a message.",
    category="Fun",
    aliases=["q", "quote"],
    usage="(reply to message) (optionally .quotly 3 to quote 3 msgs)",
    is_public=True
)
async def quotly_handler(client: Client, message: Message):
    """
    Generates a sticker quoting the replied message (and optionally next N messages).
    Usage: .q [count] (reply to start message)
    """
    try:
        if not message.has_quoted_msg:
            return await smart_reply(message, " 🗨️ Reply to a message to quote it.")

        args = extract_args(message)
        count = 1
        if args and args[0].isdigit():
            count = min(int(args[0]), 10) # Cap at 10 for performance

        status_msg = await smart_reply(message, f" 🎨 *Making quote {'(x' + str(count) + ')' if count > 1 else ''}...*")
        
        start_quoted = message.quoted
        messages_to_quote = []

        # 1. Fetch sequence if count > 1
        if count > 1:
            # We fetch messages in the chat starting from the quoted message ID
            fetched = await client.chat.fetch_messages(
                message.chat_id.serialized, 
                limit=count, 
                message_id=start_quoted.id,
                direction="after" # Fetch subsequent messages
            )
            # Prepend start_quoted if not already in fetched (usually fetch_messages includes the anchor)
            if not fetched or fetched[0].id != start_quoted.id:
                messages_to_quote.append(start_quoted)
            messages_to_quote.extend(fetched[:count])
        else:
            messages_to_quote.append(start_quoted)

        # 2. Build Multi-Message Payload
        quote_list = []
        for msg in messages_to_quote:
            text = msg.body
            if msg.is_media and not text:
                media_type_map = {
                    "image": "📸 Photo", "video": "🎥 Video",
                    "audio": "🎵 Audio", "ptt": "🎙️ Voice Note",
                    "sticker": "✨ Sticker", "document": "📄 Document"
                }
                text = media_type_map.get(msg.type.value, "📦 Media")
            
            # Resolve Identity
            # Handle both structured JID objects and raw strings
            raw_target = msg.author or msg.chat_id
            sender_id = "0"
            sender_name = "User"
            
            if raw_target:
                # Resolve target_jid string for helpers
                target_jid_str = raw_target.serialized if hasattr(raw_target, "serialized") else str(raw_target)
                sender_name = await client.get_contact_name(target_jid_str, message=msg)
                sender_id = raw_target.user if hasattr(raw_target, "user") else target_jid_str.split('@')[0]

            quote_list.append({
                "entities": [],
                "avatar": True,
                "from": {
                    "id": int(float(sender_id)) if sender_id and sender_id.isdigit() else 123456,
                    "name": sender_name,
                    "photo": {"url": "https://telegra.ph/file/18a28f73177695376046e.jpg"}
                },
                "text": text or " ",
                "replyMessage": {}
            })

        payload = {
            "type": "quote", "format": "webp", "backgroundColor": "#1b1429",
            "width": 512, "height": 768, "scale": 2,
            "messages": quote_list
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://bot.lyo.su/quote/generate", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        sticker_buffer = base64.b64decode(data['result']['image'])
                        b64_sticker = base64.b64encode(sticker_buffer).decode('utf-8')
                        
                        await client.media.send_sticker(
                            message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id), 
                            b64_sticker, 
                            reply_to=start_quoted.id
                        )
                        await status_msg.delete()
                        return
        await safe_edit(status_msg, " ⚠️ Failed to create quote sequence.")

    except Exception as e:
        await report_error(client, e, context='Quotly multi-message failure')
# --- TELEGRAPH IMAGE HOSTING ---
@astra_command(
    name="telegraph",
    description="Upload an image to Telegraph and get a direct link.",
    category="Utility",
    aliases=["tg", "host"],
    usage="(reply to an image)",
    is_public=True
)
async def telegraph_handler(client: Client, message: Message):
    """
    Uploads the replied image to Telegraph.
    """
    try:
        if not message.has_quoted_msg or not message.quoted.is_media:
            return await smart_reply(message, " 🖼️ Reply to an image to host it on Telegraph.")

        status_msg = await smart_reply(message, " 🖼️ *Uploading to Telegraph...*")

        # 1. Download Media
        file_path = await client.media.download(message.quoted)
        if not file_path:
            return await status_msg.edit(" ❌ Failed to download image.")

        # 2. Upload to Telegraph
        url = "https://telegra.ph/upload"
        
        # Prepare multipart/form-data
        import requests
        with open(file_path, 'rb') as f:
             files = {'file': ('file', f, 'image/jpeg')}
             r = requests.post(url, files=files)
        
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                tg_path = data[0]['src']
                tg_url = f"https://telegra.ph{tg_path}"
                
                await status_msg.edit(
                    f"🖼️ **Telegraph Hosted!**\n\n"
                    f"🔗 **Link:** [Direct Link]({tg_url})\n\n"
                    f"🚀 *Powered by Astra Userbot*"
                )
            else:
                await status_msg.edit(" ⚠️ Telegraph upload failed. Invalid response.")
        else:
            await status_msg.edit(f" ⚠️ Telegraph Error: status {r.status_code}")

        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await smart_reply(message, f" ❌ Telegraph Error: {str(e)}")
        await report_error(client, e, context='Telegraph command failure')
