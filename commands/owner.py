"""
Owner Commands: Profile and Account Management
--------------------------------------------
Commands to update profile info, bio, pfp, and status stories.
"""

import base64

from utils.bridge_downloader import bridge_downloader

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="setname",
    description="Update your profile display name.",
    category="Owner",
    usage="<new_name> (e.g. John Doe)",
    owner_only=True,
)
async def setname_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} New display identifier required.")

    new_name = " ".join(args)
    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Re-indexing profile name...")

    try:
        await client.account.set_name(new_name)
        await status_msg.edit(f"{UI.mono('[ OK ]')} Profile identifier synchronized: {UI.bold(new_name)}")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Synchronization failed: {UI.mono(str(e))}")


@astra_command(
    name="bio",
    description="Update your profile 'About' (Bio) text.",
    category="Owner",
    aliases=["setbio", "setabout"],
    usage="<text> (e.g. Available)",
    owner_only=True,
)
async def setbio_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} New manifest entry required.")

    new_bio = " ".join(args)
    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Updating profile manifest...")

    try:
        await client.account.set_about_text(new_bio)
        await status_msg.edit(f"{UI.mono('[ OK ]')} Profile manifest updated.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Update failure: {UI.mono(str(e))}")


@astra_command(
    name="setpfp",
    description="Update your profile picture.",
    category="Owner",
    usage="(reply to image) (e.g. .setpfp reply)",
    owner_only=True,
)
async def setpfp_handler(client: Client, message: Message):
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target image buffer required.")

    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Rendering profile asset...")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Asset extraction failed.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")

        # Call API method
        success = await client.account.update_profile_pic(media_b64)

        if success:
            await status_msg.edit(f"{UI.mono('[ OK ]')} Profile asset synchronized.")
        else:
            await status_msg.edit(f"{UI.mono('[ ERROR ]')} Profile update rejected by protocol.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Protocol failure: {UI.mono(str(e))}")


@astra_command(
    name="setgpic",
    description="Update the current group's picture.",
    category="Owner",
    aliases=["setgrouppfp"],
    usage="(reply to image) (e.g. .setgpic reply)",
    owner_only=True,
)
async def setgpic_handler(client: Client, message: Message):
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target workspace out of bounds (Group only).")
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target image buffer required.")

    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Rendering group asset...")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Asset extraction failed.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")
        success = await client.group.update_profile_pic(message.chat_id, media_b64)

        if success:
            await status_msg.edit(f"{UI.mono('[ OK ]')} Group asset synchronized.")
        else:
            await status_msg.edit(f"{UI.mono('[ ERROR ]')} Group update rejected by protocol.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Protocol failure: {UI.mono(str(e))}")


@astra_command(
    name="privacy",
    description="View or update your privacy settings.",
    category="Owner",
    usage="[category value] (e.g. last_seen all)",
    owner_only=True,
)
async def privacy_handler(client: Client, message: Message):
    args = extract_args(message)

    if not args:
        status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Fetching privacy manifest...")
        try:
            settings = await client.account.get_settings()
            text = f"{UI.header('PRIVACY MANIFEST')}\n"
            for k, v in settings.items():
                text += f"• {UI.bold(k.replace('_', ' ').title())}: {UI.mono(v)}\n"
            text += f"\n{UI.italic('Set via .privacy <category> <value>')}\n{UI.mono('Scope: last_seen, profile_pic, about, status, read_receipts')}"
            await status_msg.edit(text)
        except Exception as e:
            await status_msg.edit(f"{UI.mono('[ ERROR ]')} Manifest retrieval failure: {UI.mono(str(e))}")
        return

    if len(args) < 2:
        return await edit_or_reply(
            message,
            " ⚠️ Usage: `.privacy <category> <value>`\nCategories: last_seen, profile_pic, about, status, read_receipts\nValues: all, contacts, none",
        )

    category = args[0].lower()
    value = args[1].lower()

    # Map read_receipts bool
    if category == "read_receipts":
        value = value in ["true", "on", "yes", "enabled", "all"]

    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Synchronizing {UI.mono(category)} scope...")

    try:
        method_map = {
            "last_seen": client.account.set_last_seen,
            "profile_pic": client.account.set_profile_pic,
            "about": client.account.set_about,
            "status": client.account.set_status,
            "read_receipts": client.account.set_read_receipts,
        }

        if category not in method_map:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Invalid security scope: {UI.mono(category)}")

        await method_map[category](value)
        await status_msg.edit(f"{UI.mono('[ OK ]')} {UI.mono(category)} scope synchronized to {UI.bold(str(value))}.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Synchronization failed: {UI.mono(str(e))}")
