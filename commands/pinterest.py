
import asyncio
import os
import time
import json
import re
import shutil
import random
from config import config
from . import *
from utils.helpers import get_progress_bar, handle_command_error

@astra_command(
    name="pinterest",
    description="Download Pinterest media",
    category="Media & Downloads",
    aliases=["pin"],
    usage="<url> (Pinterest media link)",
    owner_only=False
)
async def pinterest_handler(client: Client, message: Message):
    """Download Pinterest media with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a Pinterest URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, f" 🔍 *Initializing Pinterest Engine...*")

        # Use MediaChannel for a "real-time" experience
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        
        # 1. Download
        file_path, metadata = await channel.run_bridge(url, "video")
        
        # 2. Upload
        await channel.upload_file(file_path, metadata, "video")

    except Exception as e:
        await handle_command_error(client, message, e, context='Pinterest command failure')
