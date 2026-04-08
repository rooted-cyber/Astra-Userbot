import aiohttp
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI
import time


@astra_command(
    name="github",
    description="Fetch GitHub repository or user info.",
    category="Tools & Utilities",
    aliases=["repo", "gh"],
    usage="<user/repo> or <username>",
    is_public=True,
)
async def github_handler(client: Client, message: Message):
    """GitHub info plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.bold('USAGE:')} {UI.mono('.github <user/repo>')} or {UI.mono('.github <user>')}")

    query = args[0]
    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Querying GitHub API: {UI.mono(query)}...")

    try:
        async with aiohttp.ClientSession() as session:
            if "/" in query:
                # Repo Info
                api_url = f"https://api.github.com/repos/{query}"
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = (
                            f"{UI.header('GITHUB REPOSITORY')}\n"
                            f"Name    : {UI.mono(data['full_name'])}\n"
                            f"About   : {data['description'] or 'No description'}\n"
                            f"Stars   : {UI.mono(data['stargazers_count'])} | Forks: {UI.mono(data['forks_count'])}\n"
                            f"Updated : {UI.mono(data['updated_at'][:10])}\n"
                            f"Link    : [GitHub Repo]({data['html_url']})\n"
                            f"{UI.DIVIDER}\n"
                            f"{UI.italic('Astra Development Protocol')}"
                        )
                        return await status_msg.edit(text)
            else:
                # User Info
                api_url = f"https://api.github.com/users/{query}"
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = (
                            f"{UI.header('GITHUB PROFILE')}\n"
                            f"Identity : {UI.mono(data['name'] or data['login'])}\n"
                            f"Company  : {UI.mono(data['company'] or 'N/A')}\n"
                            f"Location : {UI.mono(data['location'] or 'N/A')}\n"
                            f"Repos    : {UI.mono(data['public_repos'])}\n"
                            f"Social   : {UI.mono(f'{data['followers']} Followers')} | {UI.mono(f'{data['following']} Following')}\n"
                            f"Link     : [GitHub Profile]({data['html_url']})\n"
                            f"{UI.DIVIDER}\n"
                            f"{UI.italic('Astra Development Protocol')}"
                        )
                        return await status_msg.edit(text)

        await status_msg.edit(f"❌ Could not find GitHub info for `{query}`.")

    except Exception as e:
        await status_msg.edit(f"❌ **GitHub Error:** {str(e)}")
