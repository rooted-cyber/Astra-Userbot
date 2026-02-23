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
    name="duckduckgo",
    description="Privacy-focused web search using DuckDuckGo.",
    category="Core Tools",
    aliases=["ddg"],
    usage="<query> (e.g. .ddg Astra Bot)",
    is_public=True
)
async def ddg_handler(client: Client, message: Message):
    """DuckDuckGo search plugin."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.ddg <query>`")

    query = " ".join(args)
    status_msg = await smart_reply(message, f"🦆 Searching DDG for `{query}`...")

    try:
        # Stable SearXNG instance
        search_url = f"https://searx.work/search?q={quote_plus(query)}&format=json"
        headers = {"User-Agent": "AstraUserbot/1.0 (https://github.com/paman7647/Astra-Userbot)"}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(search_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])[:5]
                    
                    if not results:
                        return await status_msg.edit(f"❌ No results found for `{query}`.")

                    text = (
                        f"🦆 **DUCKDUCKGO SEARCH**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔎 **Query:** `{query}`\n\n"
                    )

                    # Show quick info if available
                    answer = data.get('answers', []) or data.get('infoboxes', [])
                    if answer:
                        ans_text = answer[0].get('answer') or answer[0].get('content', '')
                        if ans_text:
                            text += f"💡 **Info:** {ans_text}\n\n"

                    for i, res in enumerate(results, 1):
                        title = res.get('title', 'No Title')
                        link = res.get('url', res.get('link', '#'))
                        snippet = res.get('content', res.get('snippet', ''))[:150]
                        if snippet:
                            text += f"{i}. **[{title}]({link})**\n_{snippet}_\n\n"
                        else:
                            text += f"{i}. **[{title}]({link})**\n\n"

                    text += f"━━━━━━━━━━━━━━━━━━━━"
                    return await status_msg.edit(text)
                
        await status_msg.edit("⚠️ Failed to fetch search results. Try again later.")

    except Exception as e:
        await status_msg.edit(f"❌ **DDG Error:** {str(e)}")
