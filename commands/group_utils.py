# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import asyncio
import random
from . import *

@astra_command(
    name="pick",
    description="Pick a random user from the group.",
    category="Group Admin",
    aliases=["randomuser"],
    usage="",
    is_public=True
)
async def pick_handler(client: Client, message: Message):
    """Random user picker."""
    if not message.chat_id.endswith('@g.us'):
        return await smart_reply(message, "❌ Groups only.")
        
    status_msg = await smart_reply(message, "🎲 **Rolling the dice...**")
    
    try:
        info = await client.group.get_info(message.chat_id)
        participants = info.participants
        if not participants:
            return await status_msg.edit("❌ No participants found.")
            
        winner = random.choice(participants)
        winner_id = str(winner.id).split('@')[0]
        
        await status_msg.edit(f"🎉 **Lucky Winner:** @{winner_id}", mentions=[str(winner.id)])
    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)}")

@astra_command(
    name="tagadmin",
    description="Tag all group admins.",
    category="Group Admin",
    aliases=["admins"],
    usage="",
    is_public=True
)
async def tagadmin_handler(client: Client, message: Message):
    """Admin tagger."""
    if not message.chat_id.endswith('@g.us'):
        return await smart_reply(message, "❌ Groups only.")
        
    status_msg = await smart_reply(message, "🛡️ **Calling all admins...**")
    
    try:
        info = await client.group.get_info(message.chat_id)
        admins = [p.id for p in info.participants if p.isAdmin or p.isSuperAdmin]
        
        if not admins:
            return await status_msg.edit("❌ No admins found.")
            
        text = "🛡️ **Group Administrators:**\n\n"
        for adm in admins:
            text += f"• @{str(adm).split('@')[0]}\n"
            
        await client.send_message(message.chat_id, text, mentions=[str(a) for a in admins])
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)}")

@astra_command(
    name="sd",
    description="Send a self-destructing message.",
    category="Core Tools",
    aliases=["selfdestruct"],
    usage="<seconds> <text> (e.g. .sd 5 secret)",
    owner_only=True
)
async def sd_handler(client: Client, message: Message):
    """Self-destructing message."""
    args = extract_args(message)
    if len(args) < 2:
        return await smart_reply(message, "❌ **Usage:** `.sd <seconds> <text>`")
        
    try:
        timer = int(args[0])
        text = " ".join(args[1:])
    except ValueError:
        return await smart_reply(message, "❌ Seconds must be a number.")

    await message.delete() # Remove the command
    
    sent_msg = await client.send_message(message.chat_id, f"🕒 **Destructing in {timer}s:**\n\n{text}")
    
    await asyncio.sleep(timer)
    try:
        await client.chat.delete_messages(message.chat_id, [sent_msg.id])
    except:
        pass
