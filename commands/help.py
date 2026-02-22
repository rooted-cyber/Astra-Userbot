# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import time

@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="List all commands or get help for a specific one.",
    category="Utility",
    usage="[command/module] (optional, e.g. ping)",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Renders an interactive help menu. Features:
    1. Grid Main Menu (2-column modules)
    2. Module-wise command listing (.help <module>)
    3. Detailed command info (.help <command>)
    """
    import asyncio
    try:
        from utils.state import state
        curr_prefix = state.get_prefix()
        args = extract_args(message)

        # Pre-process categorization
        plugins = {}
        for cmd_entry in COMMANDS_METADATA:
            mod = cmd_entry.get('module', 'General')
            if mod not in plugins:
                plugins[mod] = []
            plugins[mod].append(cmd_entry)

        def get_icon(mod_name: str):
            m_low = mod_name.lower()
            if any(x in m_low for x in ["media", "instagram", "youtube", "twitter", "spotify", "pinterest", "facebook", "reddit", "soundcloud"]): return "🎥"
            if any(x in m_low for x in ["utility", "tools", "essentials"]): return "🛠️"
            if any(x in m_low for x in ["admin", "group", "protect"]): return "🛡️"
            if any(x in m_low for x in ["system", "mgmt", "bot"]): return "⚙️"
            if any(x in m_low for x in ["fun", "meme", "game", "quiz"]): return "🎭"
            if any(x in m_low for x in ["ocr", "whois", "pdf", "search"]): return "🔎"
            if "ai" in m_low: return "🤖"
            if "owner" in m_low or "sudo" in m_low: return "👑"
            return "📦"

        # 1. Handle Queries (Command or Module)
        if args:
            query = args[0].lower().strip().lstrip('.!/')
            
            # Check if it's a MODULE query
            match_mod = next((m for m in plugins.keys() if m.lower() == query or m.lower().replace('_', ' ') == query), None)
            if match_mod:
                cmd_list = sorted([c['name'] for c in plugins[match_mod]])
                mod_help = (
                    f"{get_icon(match_mod)} **{match_mod.upper()} MODULE**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Commands:** `{len(cmd_list)}`\n\n"
                    f"`{'  '.join(cmd_list)}`\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 Use `{curr_prefix}help <cmd>` for details."
                )
                return await smart_reply(message, mod_help)

            # Check if it's a COMMAND query
            cmd = next((c for c in COMMANDS_METADATA if c['name'].lower() == query or query in [a.lower() for a in c.get('aliases', [])]), None)
            if cmd:
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
                    f"🚀 *Astra Userbot Engine*"
                )
                return await smart_reply(message, help_text)
            
            return await smart_reply(message, f"❌ `{query}` not found as command or module.")

        # 2. Render Main Menu (Compact 2-Column Grid)
        status_msg = await smart_reply(message, "⚙️ *Indexing Astra Modules...*")
        
        sorted_mods = sorted(plugins.keys())
        menu_text = (
            f"🚀 **ASTRA USERBOT v4.1**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💠 **Prefix:** `{curr_prefix}`    💠 **Owner:** `Yes`\n"
            f"💠 **Modules:** `{len(plugins)}`    💠 **Commands:** `{len(COMMANDS_METADATA)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Build Grid
        for i in range(0, len(sorted_mods), 2):
            mod1 = sorted_mods[i]
            m1_display = f"{get_icon(mod1)} {mod1[:10].title()}"
            if i + 1 < len(sorted_mods):
                mod2 = sorted_mods[i+1]
                m2_display = f"{get_icon(mod2)} {mod2[:10].title()}"
                menu_text += f"🔹 {m1_display.ljust(15)} 🔹 {m2_display}\n"
            else:
                menu_text += f"🔹 {m1_display}\n"

        menu_text += (
            f"\n━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 `{curr_prefix}help <module>` to see commands.\n"
            f"✨ *Premium Userbot Performance*"
        )
        
        await status_msg.edit(menu_text)

    except Exception as e:
        await smart_reply(message, f"❌ Help Error: {e}")
