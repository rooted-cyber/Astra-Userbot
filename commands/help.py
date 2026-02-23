# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import time
from config import config

# Global cache for metadata indexing
HELP_CACHE = {
    "categories": {},
    "last_update": 0
}

@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="List all commands or get help for a specific one.",
    category="Utility",
    usage="[command/category] (optional, e.g. ping)",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Renders an interactive help menu. Features:
    1. Category-based Main Menu (2-column layout)
    2. Category-wise command listing (.help <category>)
    3. Detailed command info (.help <command>)
    """
    try:
        from utils.state import state
        curr_prefix = state.get_prefix()
        args = extract_args(message)

        # 1. Indexing / Caching Logic (Consolidated Categories)
        global HELP_CACHE
        if not HELP_CACHE["categories"]:
            HELP_CACHE["categories"] = {}
            for cmd_entry in COMMANDS_METADATA:
                cat = cmd_entry.get('category', 'Core Tools')
                
                if cat not in HELP_CACHE["categories"]:
                    HELP_CACHE["categories"][cat] = []
                HELP_CACHE["categories"][cat].append(cmd_entry)

        categories = HELP_CACHE["categories"]

        def get_icon(cat_name: str):
            c_low = cat_name.lower()
            if "media" in c_low: return "🎬"
            if "core" in c_low: return "🛠️"
            if "group" in c_low: return "👥"
            if "system" in c_low: return "⚙️"
            if "owner" in c_low: return "👑"
            if "fun" in c_low: return "🎭" 
            if "ai" in c_low: return "🧠"
            return "📦"

        # 2. Handle Queries (Command or Category)
        if args:
            query = args[0].lower().strip().lstrip('.!/')
            
            # Check for CATEGORY query
            match_cat = next((c for c in categories.keys() if c.lower() == query or c.lower().replace(' ', '_') == query), None)
            if match_cat:
                cmd_entries = sorted(categories[match_cat], key=lambda x: x['name'])
                cat_help = (
                    f"{get_icon(match_cat)} **{match_cat.upper()} COMMANDS**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Total:** `{len(cmd_entries)}` commands\n\n"
                )
                for c in cmd_entries:
                    cat_help += f"🔹 `{c['name']}` - {c['description'][:40]}...\n"
                
                cat_help += (
                    f"\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 Use `{curr_prefix}help <cmd>` for details."
                )
                return await smart_reply(message, cat_help)

            # Check for COMMAND query
            cmd = next((c for c in COMMANDS_METADATA if c['name'].lower() == query or query in [a.lower() for a in c.get('aliases', [])]), None)
            if cmd:
                help_text = (
                    f"📖 **COMMAND INFO**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Command:** `{curr_prefix}{cmd['name']}`\n"
                    f"ℹ️ **Info:** {cmd['description']}\n"
                    f"🔖 **Category:** `{cmd.get('category', 'Utility')}`\n"
                )
                if cmd.get('aliases'):
                    help_text += f"➕ **Aliases:** `{', '.join(cmd['aliases'])}`\n"
                help_text += (
                    f"💡 **Usage:** `{curr_prefix}{cmd['name']} {cmd.get('usage', '')}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 *Astra Engine v{config.VERSION}*"
                )
                return await smart_reply(message, help_text)
            
            return await smart_reply(message, f"❌ `{query}` not found as command or category.")

        # 3. Main Menu (Clean Category Grid)
        sorted_cats = sorted(categories.keys())
        menu_text = (
            f"⚡ **ASTRA USERBOT {config.VERSION_NAME}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💠 **Prefix:** `{curr_prefix}`   💠 **Cmds:** `{len(COMMANDS_METADATA)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for cat in sorted_cats:
            cmd_names = sorted([c['name'] for c in categories[cat]])
            menu_text += f"{get_icon(cat)} **{cat.upper()}**\n"
            
            # Formatted command list (clean strings)
            cmds_str = " · ".join([f"`{name}`" for name in cmd_names])
            menu_text += f"╰ {cmds_str}\n\n"

        menu_text += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 `{curr_prefix}help <category>` for details per module.\n"
            f"✨ *Premium Userbot Performance*"
        )
        
        await smart_reply(message, menu_text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        await smart_reply(message, f"❌ Help Error: {e}")
