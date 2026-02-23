# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
from urllib.parse import quote_plus
from . import *

@astra_command(
    name="song",
    description="Search and download audio from YouTube.",
    category="Downloader",
    aliases=["music"],
    usage="<song name>",
    is_public=True
)
async def song_handler(client: Client, message: Message):
    """Song downloader (audio only)."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.song <song name>`")

    query = " ".join(args)
    # Refine search query
    if "song" not in query.lower() and "audio" not in query.lower():
        query += " audio song"

    status_msg = await smart_reply(message, f"🎵 **Searching for song:** `{query}`...")

    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search YouTube for the best match
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            results = result.get('entries', [])
        
        if not results:
            return await status_msg.edit(f"❌ No song found for `{query}`.")
        
        res = results[0]
        target_url = f"https://www.youtube.com/watch?v={res.get('id')}"
        title = res.get('title')
        duration = res.get('duration_string') or (f"{int(res['duration']) // 60}:{int(res['duration']) % 60:02d}" if res.get('duration') else "N/A")
        
        await status_msg.edit(f"✅ **Found:** `{title}` ({duration})\n📥 *Downloading audio...*")

        # Use MediaChannel for download/upload
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        file_path, metadata = await channel.run_bridge(target_url, "audio")
        await channel.upload_file(file_path, metadata, "audio")
        return
                
    except Exception as e:
        await status_msg.edit(f"❌ **Song Error:** {str(e)}")

@astra_command(
    name="vsong",
    description="Search and download video from YouTube.",
    category="Downloader",
    aliases=["video"],
    usage="<video name>",
    is_public=True
)
async def vsong_handler(client: Client, message: Message):
    """Vsong downloader (video only)."""
    # ... extraction logic similar to song_handler ...
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.vsong <video name>`")

    query = " ".join(args)
    # Refine search query
    if "video" not in query.lower():
        query += " full video"

    status_msg = await smart_reply(message, f"🎬 **Searching for video:** `{query}`...")

    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search YouTube for the best match
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            results = result.get('entries', [])
        
        if not results:
            return await status_msg.edit(f"❌ No video found for `{query}`.")
        
        res = results[0]
        target_url = f"https://www.youtube.com/watch?v={res.get('id')}"
        title = res.get('title')
        duration = res.get('duration_string') or (f"{int(res['duration']) // 60}:{int(res['duration']) % 60:02d}" if res.get('duration') else "N/A")
        
        await status_msg.edit(f"✅ **Found:** `{title}` ({duration})\n📥 *Downloading video...*")

        # Use MediaChannel for download/upload
        from utils.media_channel import MediaChannel
        channel = MediaChannel(client, message, status_msg)
        file_path, metadata = await channel.run_bridge(target_url, "video")
        await channel.upload_file(file_path, metadata, "video")
        return
                
    except Exception as e:
        await status_msg.edit(f"❌ **Vsong Error:** {str(e)}")
