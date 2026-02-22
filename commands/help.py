# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import time
from . import *
@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="List all commands or get help for a specific one.",
    category="Utility",
    usage="[command] (optional, e.g. ping)",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Renders an interactive help menu by parsing the global COMMANDS_METADATA registry.
    Categories are grouped by Plugin/Module as requested.
    """
    import asyncio
    try:
        from utils.state import state
        curr_prefix = state.get_prefix()
        
        args = extract_args(message)
        
        # 1. Detailed Command Help
        if args:
            cmd_query = args[0].lower().strip().lstrip('.!/')
            cmd = next((c for c in COMMANDS_METADATA if c['name'].lower() == cmd_query or cmd_query in [a.lower() for a in c.get('aliases', [])]), None)
            
            if not cmd:
                return await smart_reply(message, f"❌ Command `{cmd_query}` not found.")
            
            help_text = (
                f"📖 **COMMAND INFO**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💠 **Command:** `{curr_prefix}{cmd['name']}`\n"
                f"ℹ️ **Info:** {cmd['description']}\n"
                f"📁 **Module:** `{cmd['module']}`\n"
                f"🔖 **Category:** `{cmd.get('category', 'General')}`\n"
            )
            
            if cmd.get('aliases'):
                help_text += f"➕ **Aliases:** `{', '.join(cmd['aliases'])}`\n"
            
            help_text += (
                f"💡 **Usage:** `{curr_prefix}{cmd['name']} {cmd.get('usage', '')}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 *Powered by Astra Userbot*"
            )
            return await smart_reply(message, help_text)

        # 2. Main Menu (Plugin-wise grouping)
        status_msg = await smart_reply(message, "📖 *Loading Astra Help Menu...*")
        await asyncio.sleep(0.3)

        # Group by Module (Plugin)
        plugins = {}
        for cmd_entry in COMMANDS_METADATA:
            mod = cmd_entry.get('module', 'General')
            if mod not in plugins:
                plugins[mod] = []
            plugins[mod].append(cmd_entry['name'])

        # Build Premium Menu
        menu_text = (
            f"🚀 **ASTRA USERBOT BETA 1**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💠 **Prefix:** `{curr_prefix}`\n"
            f"💠 **Modules:** `{len(plugins)}`\n"
            f"💠 **Commands:** `{len(COMMANDS_METADATA)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Sort plugins and add them to menu
        for mod in sorted(plugins.keys()):
            # Aesthetic icon based on module name (simple mapping)
            icon = "📦"
            m_lower = mod.lower()
            if "media" in m_lower or m_lower in ["instagram", "youtube", "twitter", "spotify", "pinterest", "facebook", "reddit", "soundcloud"]:
                icon = "🎥"
            elif "utility" in m_lower or "tools" in m_lower:
                icon = "🛠️"
            elif "admin" in m_lower or "group" in m_lower:
                icon = "🛡️"
            elif "system" in m_lower or "mgmt" in m_lower:
                icon = "⚙️"
            elif "fun" in m_lower or "meme" in m_lower:
                icon = "🎭"
            elif "ocr" in m_lower or "whois" in m_lower or "pdf" in m_lower:
                icon = "🔎"

            menu_text += f"{icon} **{mod.title()}**\n"
            cmds = sorted(plugins[mod])
            menu_text += f"`{' '.join(cmds)}`\n\n"
        
        menu_text += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Use `{curr_prefix}help <cmd>` for details.\n"
            f"✨ *Crafted with ❤️ by Astra Team*"
        )
        
        await status_msg.edit(menu_text)

    except Exception as e:
        await smart_reply(message, f"❌ Help Error: {e}")
