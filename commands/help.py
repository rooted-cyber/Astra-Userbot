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
    usage="[cmd/cat/module] (optional)",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Premium interactive help menu with module/file-wise grouping.
    """
    try:
        from utils.state import state
        curr_prefix = state.get_prefix()
        args = extract_args(message)

        # 1. Indexing Logic
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
            if "core" in c_low or "util" in c_low: return "🛠️"
            if "group" in c_low: return "👥"
            if "system" in c_low: return "⚙️"
            if "owner" in c_low: return "👑"
            if "fun" in c_low: return "🎭" 
            if "ai" in c_low: return "🧠"
            if "admin" in c_low: return "🛡️"
            if "dev" in c_low: return "🚀"
            return "📦"

        # 2. Handle Queries
        if args:
            query = args[0].lower().strip().lstrip('.!/')
            
            # A. Check for CATEGORY query
            match_cat = next((c for c in categories.keys() if c.lower() == query or c.lower().replace(' ', '_') == query), None)
            if match_cat:
                cmd_entries = sorted(categories[match_cat], key=lambda x: x['name'])
                cat_help = (
                    f"📂 **{match_cat.upper()} MODULE**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ *Category Overview*\n\n"
                )
                for c in cmd_entries:
                    cat_help += f"🔹 `{curr_prefix}{c['name']}`\n╰ {c['description'][:50]}\n\n"
                
                cat_help += (
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Total:** `{len(cmd_entries)}` commands\n"
                    f"💡 Use `{curr_prefix}help <cmd>` for specifics."
                )
                return await smart_reply(message, cat_help)

            # B. Check for MODULE (plugin) query
            match_mod = [c for c in COMMANDS_METADATA if c.get('module', '').lower() == query or c.get('module', '').lower().replace('.py', '') == query]
            if match_mod:
                match_mod = sorted(match_mod, key=lambda x: x['name'])
                mod_name = match_mod[0].get('module', query).title()
                mod_help = (
                    f"📦 **PLUGIN: {mod_name}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛠️ *Commands in this file:*\n\n"
                )
                for c in match_mod:
                    mod_help += f"🔸 `{curr_prefix}{c['name']}`\n"
                
                mod_help += (
                    f"\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Total:** `{len(match_mod)}` commands\n"
                    f"✨ *Astra Plugin Architecture*"
                )
                return await smart_reply(message, mod_help)

            # C. Check for COMMAND query
            cmd = next((c for c in COMMANDS_METADATA if c['name'].lower() == query or query in [a.lower() for a in c.get('aliases', [])]), None)
            if cmd:
                # Get other commands in same module
                peer_cmds = [c['name'] for c in COMMANDS_METADATA if c.get('module') == cmd.get('module') and c['name'] != cmd['name']]
                
                help_text = (
                    f"📖 **COMMAND INDEX**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💠 **Command:** `{curr_prefix}{cmd['name']}`\n"
                    f"ℹ️ **Info:** _{cmd['description']}_\n"
                    f"🔖 **Category:** `{cmd.get('category', 'Utility')}`\n"
                )
                if cmd.get('aliases'):
                    help_text += f"➕ **Aliases:** `{', '.join(cmd['aliases'])}`\n"
                
                help_text += f"💡 **Usage:** `{curr_prefix}{cmd['name']} {cmd.get('usage', '')}`\n"
                
                if peer_cmds:
                    # Clean grouping of related commands
                    help_text += (
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔗 **Related in `{cmd.get('module')}`:**\n"
                        f"╰ " + " · ".join([f"`{p}`" for p in peer_cmds[:8]]) + (f" ...and {len(peer_cmds)-8} more" if len(peer_cmds) > 8 else "") + "\n"
                    )

                help_text += (
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 *Astra Engine v{config.VERSION}*"
                )
                return await smart_reply(message, help_text)
            
            return await smart_reply(message, f"❌ `{query}` not found as command, category, or plugin.")

        # 3. Main Menu (Clean Category Grid)
        sorted_cats = sorted(categories.keys())
        menu_text = (
            f"⚡ **ASTRA USERBOT {config.VERSION_NAME}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **Owner:** `{config.OWNER_ID}`\n"
            f"💠 **Prefix:** `{curr_prefix}`    💠 **Cmds:** `{len(COMMANDS_METADATA)}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for cat in sorted_cats:
            cmd_names = sorted([c['name'] for c in categories[cat]])
            menu_text += f"{get_icon(cat)} **{cat.upper()}**\n"
            
            # Formatted command list
            cmds_str = "  ·  ".join([f"`{name}`" for name in cmd_names])
            menu_text += f"╰ {cmds_str}\n\n"

        menu_text += (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 `{curr_prefix}help <module>` for per-file details.\n"
            f"✨ *Premium Performance & Aesthetics*"
        )
        
        await smart_reply(message, menu_text)

    except Exception as e:
        import traceback
        logger.error(f"Help Error: {e}\n{traceback.format_exc()}")
        await smart_reply(message, f"❌ Help System Failure: {e}")

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        await smart_reply(message, f"❌ Help Error: {e}")
