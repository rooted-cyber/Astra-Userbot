# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import asyncio
import os
import time
import json
import re
import shutil
import random
from config import config
from . import *
from utils.helpers import get_progress_bar

@astra_command(
    name="spotify",
    description="Download/Search Spotify track",
    category="Media Engine",
    aliases=[],
    usage="<query|url> (search term or Spotify link)",
    owner_only=False
)
async def spotify_handler(client: Client, message: Message):
    """Download/Search Spotify track with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Provide a Spotify link or song name.")

        query = " ".join(args_list)
        status_msg = await smart_reply(message, f" 🔍 *Initializing Spotify Engine...*")

        # Searching on YouTube as fallback/source for downloads
        search_query = f"ytsearch:{query}" if "spotify.com" not in query else query

        # Use MediaChannel for a "real-time" experience
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        
        # 1. Download
        file_path, metadata = await channel.run_bridge(search_query, "audio")
        
        # 2. Upload
        await channel.upload_file(file_path, metadata, "audio")

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Spotify command root failure')

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Spotify command root failure')
