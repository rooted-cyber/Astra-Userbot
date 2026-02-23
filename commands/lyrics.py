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
    name="lyrics",
    description="Fetch lyrics for a song.",
    category="Core Tools",
    aliases=["lyrical"],
    usage="<song name> [artist] (e.g. .lyrics Blinding Lights)",
    is_public=True
)
async def lyrics_handler(client: Client, message: Message):
    """Lyrics lookup plugin."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.lyrics <song name>`")

    query = " ".join(args)
    status_msg = await smart_reply(message, f"🎵 **Searching lyrics for:** `{query}`...")

    try:
        # Using a reliable free lyrics API (some lyrics APIs are tricky, 
        # using a common public proxy or search as fallback)
        # lyrics.ovh is a popular free Choice
        api_url = f"https://api.lyrics.ovh/suggest/{quote_plus(query)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    suggestions = data.get('data', [])
                    
                    if not suggestions:
                        return await status_msg.edit(f"❌ No lyrics found for `{query}`.")

                    # Get the most relevant suggestion
                    best_match = suggestions[0]
                    artist = best_match['artist']['name']
                    title = best_match['title']
                    
                    # Fetch actual lyrics
                    lyrics_api = f"https://api.lyrics.ovh/v1/{quote_plus(artist)}/{quote_plus(title)}"
                    async with session.get(lyrics_api) as l_resp:
                        if l_resp.status == 200:
                            l_data = await l_resp.json()
                            lyrics = l_data.get('lyrics', '')
                            
                            if not lyrics:
                                return await status_msg.edit(f"❌ Could not retrieve full lyrics for `{title}` by `{artist}`.")

                            # Formatting lyrics (cap at max message length if needed)
                            final_lyrics = lyrics.strip()
                            if len(final_lyrics) > 3000:
                                final_lyrics = final_lyrics[:3000] + "..."

                            text = (
                                f"🎶 **LYRICS ENGINE**\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"🆔 **Song:** `{title}`\n"
                                f"👤 **Artist:** `{artist}`\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                                f"{final_lyrics}\n\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"🚀 *Powered by Astra*"
                            )
                            return await status_msg.edit(text)

        await status_msg.edit(f"⚠️ Lyrics not found for `{query}`. Try adding the artist name.")

    except Exception as e:
        await status_msg.edit(f"❌ **Lyrics Error:** {str(e)}")
