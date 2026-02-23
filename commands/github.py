# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
from . import *

@astra_command(
    name="github",
    description="Fetch GitHub repository or user info.",
    category="Core Tools",
    aliases=["repo", "gh"],
    usage="<user/repo> or <username>",
    is_public=True
)
async def github_handler(client: Client, message: Message):
    """GitHub info plugin."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ **Usage:** `.github <username>` or `.github <user/repo>`")

    query = args[0]
    status_msg = await smart_reply(message, f"🐙 **Fetching GitHub info for:** `{query}`...")

    try:
        async with aiohttp.ClientSession() as session:
            if "/" in query:
                # Repo Info
                api_url = f"https://api.github.com/repos/{query}"
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = (
                            f"📦 **GITHUB REPOSITORY**\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📁 **Name:** `{data['full_name']}`\n"
                            f"📝 **About:** {data['description'] or 'No description'}\n"
                            f"⭐ **Stars:** `{data['stargazers_count']}`    🍴 **Forks:** `{data['forks_count']}`\n"
                            f"🕒 **Updated:** `{data['updated_at'][:10]}`\n"
                            f"🔗 **Link:** [GitHub Repo]({data['html_url']})\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🚀 *Astra Dev Tools*"
                        )
                        return await status_msg.edit(text)
            else:
                # User Info
                api_url = f"https://api.github.com/users/{query}"
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = (
                            f"👤 **GITHUB PROFILE**\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🆔 **Name:** `{data['name'] or data['login']}`\n"
                            f"🏢 **Company:** `{data['company'] or 'N/A'}`\n"
                            f"📍 **Location:** `{data['location'] or 'N/A'}`\n"
                            f"📦 **Public Repos:** `{data['public_repos']}`\n"
                            f"👥 **Followers:** `{data['followers']}`    🤝 **Following:** `{data['following']}`\n"
                            f"🔗 **Link:** [GitHub Profile]({data['html_url']})\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🚀 *Astra Dev Tools*"
                        )
                        return await status_msg.edit(text)

        await status_msg.edit(f"❌ Could not find GitHub info for `{query}`.")

    except Exception as e:
        await status_msg.edit(f"❌ **GitHub Error:** {str(e)}")
