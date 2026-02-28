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
    name="ytsearch",
    description="Search for videos on YouTube and get links.",
    category="Media & Downloads",
    aliases=["yts"],
    usage="<query> (e.g. .yts never gonna give you up)",
    is_public=True
)
async def ytsearch_handler(client: Client, message: Message):
    """YouTube search plugin."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.ytsearch <query>`")

    query = " ".join(args)
    status_msg = await smart_reply(message, f"📺 Searching YouTube for `{query}`...")

    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # yt-dlp search is very reliable
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = result.get('entries', [])
        
        if not results:
            return await status_msg.edit(f"❌ No results found on YouTube for `{query}`.")

        text = (
            f"📺 **YOUTUBE SEARCH**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **Query:** `{query}`\n\n"
        )

        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            link = f"https://www.youtube.com/watch?v={res.get('id')}"
            duration = res.get('duration_string', 'N/A')
            views = res.get('view_count', 'N/A')
            
            text += (
                f"{i}. **{title}**\n"
                f"   🕒 `{duration}` | 👁️ `{views}`\n"
                f"   🔗 {link}\n\n"
            )

        text += f"━━━━━━━━━━━━━━━━━━━━\n💡 Use `.youtube <link>` to download."
        return await status_msg.edit(text)
                
    except Exception as e:
        await status_msg.edit(f"❌ **YouTube Search Error:** {str(e)}")
