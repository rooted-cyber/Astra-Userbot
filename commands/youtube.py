# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import shutil
import asyncio
import json
import re
import random
import time
from . import *
from config import config
from utils.helpers import get_progress_bar, safe_edit

@astra_command(
    name="youtube",
    description="Download media from YouTube (Audio or Video).",
    category="Media Engine",
    aliases=["yt", "ytdl"],
    usage="<url> [video|audio] [--doc] (e.g. .youtube <link> video)",
    owner_only=False
)
async def youtube_handler(client: Client, message: Message):
    """
    Handles media download requests with optimized MediaChannel.
    """
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a valid YouTube URL.")

        url_input = args_list[0]
        args_lower = [arg.lower() for arg in args_list]
        
        # Mode detection
        video_keywords = ["video", "vid", "mp4", "mkv", "720p", "1080p"]
        mode = "video" if any(kw in args_lower for kw in video_keywords) else "audio"

        status_msg = await smart_reply(message, f" 🔍 *Initializing Astra Media Engine...*")

        # Auto-Search Logic
        url = url_input
        if not url_input.startswith(("http://", "https://", "www.")):
            await status_msg.edit(f"📺 **Searching for:** `{url_input}`...")
            search_query = " ".join(args_list) # Use full args as query
            if " video" in search_query.lower() or " audio" in search_query.lower():
                search_query = search_query.rsplit(' ', 1)[0] # Strip mode for search

            search_url = f"https://api.disroot.org/search/youtube/search?q={quote_plus(search_query)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get('results', [])
                        if results:
                            url = results[0]['url']
                            await status_msg.edit(f"✅ **Found:** `{results[0]['title']}`\n📥 *Downloading...*")
                        else:
                            return await status_msg.edit(f"❌ No results found for `{search_query}`.")
                    else:
                        return await status_msg.edit("⚠️ Search engine failed. Please provide a direct link.")
        
        # Use MediaChannel for a "real-time" experience
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        
        # 1. Download
        file_path, metadata = await channel.run_bridge(url, mode)
        
        # 2. Upload
        await channel.upload_file(file_path, metadata, mode)

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='YouTube command root failure')
