# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

"""
Owner Commands: Profile and Account Management
--------------------------------------------
Commands to update profile info, bio, pfp, and status stories.
"""

from . import *
import os
import base64
import time
@astra_command(
    name="setname",
    description="Update your profile display name.",
    category="Owner Utility",
    usage="<new_name> (e.g. John Doe)",
    owner_only=True
)
async def setname_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await smart_reply(message, " ⚠️ Provide a new name. Usage: `.setname My New Name`")
    
    new_name = " ".join(args)
    status_msg = await smart_reply(message, f" 🔄 Updating profile name to: *{new_name}*...")
    
    try:
        await client.account.set_name(new_name)
        await status_msg.edit(f" ✅ Profile name updated to: *{new_name}*")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update name: {str(e)}")

@astra_command(
    name="bio",
    description="Update your profile 'About' (Bio) text.",
    category="Owner Utility",
    aliases=["setbio", "setabout"],
    usage="<text> (e.g. Available)",
    owner_only=True
)
async def setbio_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await smart_reply(message, " ⚠️ Provide a bio text. Usage: `.bio Available`")
    
    new_bio = " ".join(args)
    status_msg = await smart_reply(message, " 🔄 Updating profile bio...")
    
    try:
        await client.account.set_about_text(new_bio)
        await status_msg.edit(f" ✅ Bio updated to: *{new_bio}*")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update bio: {str(e)}")

@astra_command(
    name="status",
    description="Post a text or media status update (Story).",
    category="Owner Utility",
    aliases=["setstatus", "post"],
    usage="<text/reply media> (reply to a message or supply text)",
    owner_only=True
)
async def status_handler(client: Client, message: Message):
    args = extract_args(message)
    
    if message.has_quoted_msg and message.quoted.is_media:
        status_msg = await smart_reply(message, " ⏳ *Uploading media to status...*")
        try:
            # Download quoted media
            media_b64 = await client.media.download_media(message.quoted.id if message.quoted else message.quoted_message_id)
            caption = " ".join(args) if args else ""
            
            # Determine type
            mime = message.quoted.mimetype
            mtype = 'image' if 'image' in mime else 'video'
            
            await client.api.send_media_status(media_b64, mtype, caption)
            await status_msg.edit(" ✅ Media status posted successfully!")
        except Exception as e:
            await status_msg.edit(f" ❌ Failed to post media status: {str(e)}")
        return

    if not args:
        return await smart_reply(message, " ⚠️ Provide text or reply to media to post a status Story.")
    
    text = " ".join(args)
    status_msg = await smart_reply(message, " ⏳ *Posting text status...*")
    
    try:
        await client.account.post_status(text)
        await status_msg.edit(" ✅ Text status posted successfully!")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to post status: {str(e)}")

@astra_command(
    name="setpfp",
    description="Update your profile picture.",
    category="Owner Utility",
    usage="(reply to image) (e.g. .setpfp reply)",
    owner_only=True
)
async def setpfp_handler(client: Client, message: Message):
    if not message.has_quoted_msg or not message.quoted.is_media or 'image' not in message.quoted.mimetype:
        return await smart_reply(message, " ⚠️ Reply to an image to set it as your profile picture.")
    
    status_msg = await smart_reply(message, " ⏳ *Updating profile picture...*")
    
    try:
        # PFP Update usually requires a bridge method or direct Job call
        # We'll use a direct bridge call for maximum reliability
        media_b64 = await client.media.download_media(message.quoted.id if message.quoted else message.quoted_message_id)
        
        # Call API method
        success = await client.account.update_profile_pic(media_b64)
        
        if success:
            await status_msg.edit(" ✅ Profile picture updated successfully!")
        else:
            await status_msg.edit(" ❌ Profile picture update returned false.")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update PFP: {str(e)}")

@astra_command(
    name="setgpic",
    description="Update the current group's picture.",
    category="Owner Utility",
    aliases=["setgrouppfp"],
    usage="(reply to image) (e.g. .setgpic reply)",
    owner_only=True
)
async def setgpic_handler(client: Client, message: Message):
    if not message.is_group:
        return await smart_reply(message, " ❌ This command only works in groups.")
    if not message.has_quoted_msg or not message.quoted.is_media or 'image' not in message.quoted.mimetype:
        return await smart_reply(message, " ⚠️ Reply to an image to set it as group picture.")
    
    status_msg = await smart_reply(message, " ⏳ *Updating group picture...*")
    
    try:
        media_b64 = await client.media.download_media(message.quoted.id if message.quoted else message.quoted_message_id)
        success = await client.group.update_profile_pic(message.chat_id, media_b64)
        
        if success:
            await status_msg.edit(" ✅ Group picture updated successfully!")
        else:
            await status_msg.edit(" ❌ Group picture update returned false.")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update group PFP: {str(e)}")

@astra_command(
    name="privacy",
    description="View or update your privacy settings.",
    category="Owner Utility",
    usage="[category value] (e.g. last_seen all)",
    owner_only=True
)
async def privacy_handler(client: Client, message: Message):
    args = extract_args(message)
    
    if not args:
        status_msg = await smart_reply(message, " 🔍 *Fetching privacy settings...*")
        try:
            settings = await client.account.get_settings()
            text = " 🛡️ **Privacy Settings**\n\n"
            for k, v in settings.items():
                text += f" • *{k.replace('_', ' ').title()}:* `{v}`\n"
            text += "\n_Use `.privacy <category> <value>` to update._\n_Categories: last_seen, profile_pic, about, status, read_receipts_"
            await status_msg.edit(text)
        except Exception as e:
            await status_msg.edit(f" ❌ Failed to fetch settings: {str(e)}")
        return

    if len(args) < 2:
        return await smart_reply(message, " ⚠️ Usage: `.privacy <category> <value>`\nCategories: last_seen, profile_pic, about, status, read_receipts\nValues: all, contacts, none")

    category = args[0].lower()
    value = args[1].lower()
    
    # Map read_receipts bool
    if category == 'read_receipts':
        value = value in ['true', 'on', 'yes', 'enabled', 'all']

    status_msg = await smart_reply(message, f" 🔄 Updating *{category}* to *{value}*...")
    
    try:
        method_map = {
            'last_seen': client.account.set_last_seen,
            'profile_pic': client.account.set_profile_pic,
            'about': client.account.set_about,
            'status': client.account.set_status,
            'read_receipts': client.account.set_read_receipts
        }
        
        if category not in method_map:
            return await status_msg.edit(f" ❌ Invalid category: {category}")
            
        await method_map[category](value)
        await status_msg.edit(f" ✅ Privacy setting *{category}* updated to *{value}*!")
    except Exception as e:
        await status_msg.edit(f" ❌ Privacy update failed: {str(e)}")
