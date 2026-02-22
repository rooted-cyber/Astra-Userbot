# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import time
from . import *

@astra_command(
    name="whois",
    description="Fetch detailed information about a user.",
    category="Astra Essentials",
    aliases=["info", "user"],
    usage="<reply|@mention|phone>",
    owner_only=False
)
async def whois_handler(client: Client, message: Message):
    """Detailed user/contact information tracker."""
    try:
        args_list = extract_args(message)
        target_jid = ""

        # 1. Resolve Target
        if message.has_quoted_msg:
            target_jid = message.quoted.sender or message.quoted.chat_id
        elif message.mentioned_jids:
            target_jid = message.mentioned_jids[0]
        elif args_list:
            raw = args_list[0].replace('@', '').strip()
            if raw.isdigit():
                target_jid = f"{raw}@c.us"
            else:
                target_jid = raw
        else:
            # Info about self or the current chat
            target_jid = message.sender or (message.chat_id if not message.chat_id.endswith('@g.us') else "")

        if not target_jid:
            return await smart_reply(message, " 👤 Provide a user to fetch info.")

        status_msg = await smart_reply(message, " 🔍 *Fetching user intelligence...*")

        # 2. Extract Data
        # Normalize JID for display
        jid_str = target_jid.serialized if hasattr(target_jid, "serialized") else str(target_jid)
        user_id = jid_str.split('@')[0]
        
        # Fetch Contact/User details
        contact = await client.get_contact(jid_str)
        name = contact.name or contact.push_name or contact.verified_name or "Unknown"
        
        # Check if Business
        is_business = "Yes" if contact.is_business else "No"
        
        # About/Status
        about = "N/A" # Status fetching is currently unsupported natively by Astra
        
        # Profile Pic
        pic_url = "https://telegra.ph/file/18a28f73177695376046e.jpg"
        try:
            target_pic = await client.bridge.call("getProfilePicUrl", jid_str)
            if target_pic:
                pic_url = target_pic
        except:
            pass

        # 3. Build Response
        info_text = (
            f"👤 **USER INFORMATION**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Name:** `{name}`\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"🏢 **Business:** `{is_business}`\n"
            f"📜 **About:** `{about}`\n"
            f"🔗 **JID:** `{jid_str}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 *Powered by Astra Userbot*"
        )

        # Send as image if pic available, else text
        if pic_url:
            await client.send_message(message.chat_id, info_text, media_url=pic_url)
        else:
            await status_msg.edit(info_text)
            
        if status_msg and pic_url:
             await status_msg.delete()

    except Exception as e:
        await smart_reply(message, f" ❌ Whois Error: {str(e)}")
        await report_error(client, e, context='Whois command failure')
