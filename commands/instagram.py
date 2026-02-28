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
    name="instagram",
    description="Download Instagram post/reel",
    category="Media & Downloads",
    aliases=["ig", "reel"],
    usage="<url> (Instagram post/reel link)",
    owner_only=False
)
async def instagram_handler(client: Client, message: Message):
    """Download Instagram post/reel with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide an Instagram URL.")

        url = args_list[0]
        args_lower = [arg.lower() for arg in args_list]
        mode = "audio" if "audio" in args_lower or "mp3" in args_lower else "video"

        status_msg = await smart_reply(message, f" 🔍 *Initializing Instagram Engine...*")

        # Use MediaChannel for a "real-time" experience
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        
        # 1. Download
        file_path, metadata = await channel.run_bridge(url, mode)
        
        # 2. Upload
        await channel.upload_file(file_path, metadata, mode)

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Instagram command root failure')
