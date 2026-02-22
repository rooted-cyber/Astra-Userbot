# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

from . import *
from utils.media_channel import MediaChannel

@astra_command(
    name="tiktok",
    description="Download TikTok video (No watermark)",
    category="Media",
    aliases=["tt"],
    usage="<url> (TikTok link)",
    owner_only=False
)
async def tiktok_handler(client: Client, message: Message):
    """Download TikTok video with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a TikTok URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, f" 🔍 *Initializing TikTok Engine...*")

        # Use MediaChannel for a "real-time" experience
        channel = MediaChannel(client, message, status_msg)
        
        # 1. Download (JS bridge handles the extraction)
        file_path, metadata = await channel.run_bridge(url, "video")
        
        # 2. Upload
        await channel.upload_file(file_path, metadata, "video")

    except Exception as e:
        await smart_reply(message, f" ❌ TikTok Core Error: {str(e)}")
        await report_error(client, e, context='TikTok command failure')
