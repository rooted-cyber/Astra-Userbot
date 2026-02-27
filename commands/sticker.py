# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import os
import base64
import asyncio
from . import *
from utils.bridge_downloader import bridge_downloader

@astra_command(
    name="sticker",
    description="Convert an image or video to a sticker.",
    category="Core Tools",
    aliases=["s", "stkr"],
    usage="(reply to image/video)",
    is_public=True
)
async def sticker_handler(client: Client, message: Message):
    """Sticker creation plugin."""
    try:
        quoted = message.quoted if message.has_quoted_msg else None
        target = quoted if quoted and quoted.is_media else (message if message.is_media else None)

        if not target:
            return await smart_reply(message, "✨ Reply to an image or video to make a sticker.")

        status_msg = await smart_reply(message, "✨ **Making your sticker...**")

        # Download media via high-reliability Bridge
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit("❌ Failed to download media.")

        b64_data = base64.b64encode(media_data).decode('utf-8')
        mimetype = target.mimetype

        # Send as sticker
        # The bridge's media.send_sticker handles the conversion/optimization
        await client.media.send_sticker(
            message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id),
            b64_data,
            reply_to=target.id
        )
        
        await status_msg.delete()

    except Exception as e:
        await smart_reply(message, f"❌ **Sticker Error:** {str(e)}")

@astra_command(
    name="tiny",
    description="Create a tiny sticker (centered image).",
    category="Core Tools",
    usage="(reply to image)",
    is_public=True
)
async def tiny_handler(client: Client, message: Message):
    """Tiny sticker plugin - logic handled via bridge media params if supported or just placeholder."""
    # This usually requires ffmpeg pad filter, but we'll try basic first
    await sticker_handler(client, message)
