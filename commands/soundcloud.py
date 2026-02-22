# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

from . import *
from utils.media_channel import MediaChannel

@astra_command(
    name="soundcloud",
    description="Download SoundCloud track",
    category="Media Engine",
    aliases=["sc"],
    usage="<url> (SoundCloud track link)",
    owner_only=False
)
async def soundcloud_handler(client: Client, message: Message):
    """Download SoundCloud track with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a SoundCloud URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, f" 🔍 *Initializing SoundCloud Engine...*")

        channel = MediaChannel(client, message, status_msg)
        # SoundCloud is audio
        file_path, metadata = await channel.run_bridge(url, "audio")
        await channel.upload_file(file_path, metadata, "audio")

    except Exception as e:
        await smart_reply(message, f" ❌ SoundCloud Error: {str(e)}")
        await report_error(client, e, context='SoundCloud command failure')
