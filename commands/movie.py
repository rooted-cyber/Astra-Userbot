# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
import base64
from . import *

@astra_command(
    name="movie",
    description="Search for movie or series information.",
    category="Core Tools",
    aliases=["imdb", "series"],
    usage="<movie name> (e.g. .movie Interstellar)",
    is_public=True
)
async def movie_handler(client: Client, message: Message):
    """Movie/Series lookup plugin using OMDb API."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.movie <movie name>`")

    query = " ".join(args)
    status_msg = await smart_reply(message, f"🎬 **Searching for Movie:** `{query}`...")

    try:
        # Using a public OMDb API key (common for open source tools)
        # Note: If this key expires, users can set their own in config.
        api_key = "bc7b70c3" 
        api_url = f"http://www.omdbapi.com/?apikey={api_key}&t={query}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get('Response') == 'False':
                        return await status_msg.edit(f"❌ No movie found for `{query}`: {data.get('Error')}")

                    title = data.get('Title')
                    year = data.get('Year')
                    rating = data.get('imdbRating')
                    runtime = data.get('Runtime')
                    genre = data.get('Genre')
                    plot = data.get('Plot', 'No plot available.')
                    poster_url = data.get('Poster')
                    imdb_id = data.get('imdbID')

                    text = (
                        f"🎬 **MOVIE DATABASE**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 **Title:** `{title}` ({year})\n"
                        f"🌟 **Rating:** `{rating}` | 🕒 `{runtime}`\n"
                        f"🎭 **Genre:** `{genre}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{plot}\n\n"
                        f"🔗 [IMDb Link](https://www.imdb.com/title/{imdb_id})\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🚀 *Powered by Astra*"
                    )

                    if poster_url and poster_url != "N/A":
                        async with session.get(poster_url) as img_resp:
                            if img_resp.status == 200:
                                img_data = await img_resp.read()
                                b64_data = base64.b64encode(img_data).decode('utf-8')
                                media = {
                                    "mimetype": "image/jpeg",
                                    "data": b64_data,
                                    "filename": f"movie_{imdb_id}.jpg"
                                }
                                await client.send_media(message.chat_id, media, caption=text)
                                return await status_msg.delete()

                    return await status_msg.edit(text)
                
        await status_msg.edit("⚠️ Movie service is currently unavailable.")

    except Exception as e:
        await status_msg.edit(f"❌ **Movie Error:** {str(e)}")
