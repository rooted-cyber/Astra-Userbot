# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import time
import logging
from config import config

logger = logging.getLogger("Astra.Help")

# ─────── Category Normalization Map ───────
# Maps raw category strings → unified display categories
CATEGORY_MAP = {
    # AI
    "ai intelligence": "AI & Search",
    # Tools / Utility / Essentials → merged
    "astra essentials": "Tools & Utilities",
    "core tools":       "Tools & Utilities",
    "utility":          "Tools & Utilities",
    "general":          "Tools & Utilities",
    # Fun
    "fun":              "Fun & Memes",
    "fun & games":      "Fun & Memes",
    # Media
    "downloader":       "Media & Downloads",
    "media engine":     "Media & Downloads",
    # Group
    "group admin":      "Group Management",
    # Owner
    "owner tools":      "Owner",
    "owner utility":    "Owner",
    # System
    "system":           "System",
    "system & bot":     "System",
    "system hub":       "System",
}

# Icons per unified category
CATEGORY_ICONS = {
    "AI & Search":        "🧠",
    "Tools & Utilities":  "🛠️",
    "Fun & Memes":        "🎭",
    "Media & Downloads":  "🎬",
    "Group Management":   "👥",
    "Owner":              "👑",
    "System":             "⚙️",
}

# Sort order for main menu
CATEGORY_ORDER = [
    "AI & Search",
    "Tools & Utilities",
    "Fun & Memes",
    "Media & Downloads",
    "Group Management",
    "Owner",
    "System",
]

def normalize_category(raw_cat: str) -> str:
    """Normalizes a raw category string to a unified display category."""
    return CATEGORY_MAP.get(raw_cat.lower().strip(), raw_cat)

def get_icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, "📦")


# ─────── Help Cache ───────
HELP_CACHE = {
    "merged": {},      # { unified_cat: [cmd_entry, ...] }
    "by_module": {},   # { module_name: [cmd_entry, ...] }
    "built": False
}

def _build_cache():
    """Indexes COMMANDS_METADATA into merged categories and module groups."""
    HELP_CACHE["merged"].clear()
    HELP_CACHE["by_module"].clear()
    
    for cmd in COMMANDS_METADATA:
        # Merged category
        ucat = normalize_category(cmd.get('category', 'Tools & Utilities'))
        HELP_CACHE["merged"].setdefault(ucat, []).append(cmd)
        
        # Module index
        mod = cmd.get('module', 'unknown')
        HELP_CACHE["by_module"].setdefault(mod, []).append(cmd)
    
    HELP_CACHE["built"] = True


@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="Show all commands, category, or plugin details.",
    category="Tools & Utilities",
    usage="[cmd / category / module]",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Premium help system with unified categories and module grouping.
    """
    try:
        from utils.state import state
        pfx = state.get_prefix()
        args = extract_args(message)

        # Rebuild cache on every call to stay fresh after reloads
        _build_cache()
        merged = HELP_CACHE["merged"]
        by_mod = HELP_CACHE["by_module"]

        # ── QUERY MODE ──────────────────────────
        if args:
            q = args[0].lower().strip().lstrip('.!/')
            
            # ① MODULE / PLUGIN search (e.g. ".help meme", ".help system_mgmt")
            mod_match = by_mod.get(q)
            if mod_match:
                cmds = sorted(mod_match, key=lambda c: c['name'])
                cats_in_mod = sorted(set(normalize_category(c.get('category', '')) for c in cmds))
                
                txt = (
                    f"╔═══════════════════════╗\n"
                    f"║  📦 PLUGIN: *{q.upper()}*\n"
                    f"╚═══════════════════════╝\n\n"
                )
                for c in cmds:
                    txt += f"  ▸ `{pfx}{c['name']}`  —  _{c['description'][:45]}_\n"
                txt += (
                    f"\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                    f"  📂 Categories: {', '.join(cats_in_mod)}\n"
                    f"  � Total: *{len(cmds)}* commands\n"
                    f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                    f"💡 `{pfx}help <cmd>` for usage details"
                )
                return await smart_reply(message, txt)

            # ② CATEGORY search (e.g. ".help fun & memes")
            full_query = " ".join(args).lower().strip()
            cat_match = next((c for c in merged if c.lower() == full_query or c.lower().replace(' ', '_') == q or c.lower().replace('&', 'and').replace(' ', '_') == q), None)
            if cat_match:
                cmds = sorted(merged[cat_match], key=lambda c: c['name'])
                icon = get_icon(cat_match)
                
                txt = (
                    f"╔═══════════════════════╗\n"
                    f"║  {icon} *{cat_match.upper()}*\n"
                    f"╚═══════════════════════╝\n\n"
                )
                for c in cmds:
                    txt += f"  ▸ `{pfx}{c['name']}`  —  _{c['description'][:45]}_\n"
                txt += (
                    f"\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                    f"  � Total: *{len(cmds)}* commands\n"
                    f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                    f"💡 `{pfx}help <cmd>` for usage details"
                )
                return await smart_reply(message, txt)

            # ③ COMMAND search (e.g. ".help ping")
            cmd = next((c for c in COMMANDS_METADATA if c['name'].lower() == q or q in [a.lower() for a in c.get('aliases', [])]), None)
            if cmd:
                mod_name = cmd.get('module', '?')
                peer_cmds = [c['name'] for c in COMMANDS_METADATA if c.get('module') == mod_name and c['name'] != cmd['name']]
                
                txt = (
                    f"╔═══════════════════════╗\n"
                    f"║  📖 *COMMAND DETAILS*\n"
                    f"╚═══════════════════════╝\n\n"
                    f"  💠 *Command:*  `{pfx}{cmd['name']}`\n"
                    f"  ℹ️ *Info:*  _{cmd['description']}_\n"
                    f"  � *Category:*  {normalize_category(cmd.get('category', ''))}\n"
                    f"  📦 *Plugin:*  `{mod_name}`\n"
                )
                if cmd.get('aliases'):
                    txt += f"  ➕ *Aliases:*  {', '.join(['`' + a + '`' for a in cmd['aliases']])}\n"
                txt += f"  💡 *Usage:*  `{pfx}{cmd['name']} {cmd.get('usage', '')}`\n"
                
                if peer_cmds:
                    peers_str = "  ·  ".join([f"`{p}`" for p in sorted(peer_cmds)[:10]])
                    extra = f" +{len(peer_cmds)-10} more" if len(peer_cmds) > 10 else ""
                    txt += (
                        f"\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                        f"  🔗 *Also in `{mod_name}`:*\n"
                        f"  {peers_str}{extra}\n"
                    )
                
                txt += (
                    f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
                    f"⚡ *Astra Engine v{config.VERSION}*"
                )
                return await smart_reply(message, txt)

            return await smart_reply(message, f"❌ `{q}` not found.\n💡 Try `{pfx}help` for the full menu.")

        # ── MAIN MENU ───────────────────────────
        total = len(COMMANDS_METADATA)
        
        txt = (
            f"╔═══════════════════════╗\n"
            f"║   ⚡ *ASTRA USERBOT*  ⚡\n"
            f"║   {config.VERSION_NAME}\n"
            f"╚═══════════════════════╝\n\n"
            f"  � *Owner:*  `{config.OWNER_ID}`\n"
            f"  � *Prefix:*  `{pfx}`    � *Commands:*  `{total}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for cat in CATEGORY_ORDER:
            if cat not in merged:
                continue
            cmds = sorted(merged[cat], key=lambda c: c['name'])
            icon = get_icon(cat)
            names = "  ·  ".join([f"`{c['name']}`" for c in cmds])
            txt += f"{icon} *{cat.upper()}*  [{len(cmds)}]\n╰ {names}\n\n"
        
        # Any uncategorized leftovers
        for cat in sorted(merged.keys()):
            if cat not in CATEGORY_ORDER:
                cmds = sorted(merged[cat], key=lambda c: c['name'])
                names = "  ·  ".join([f"`{c['name']}`" for c in cmds])
                txt += f"📦 *{cat.upper()}*  [{len(cmds)}]\n╰ {names}\n\n"

        txt += (
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 `{pfx}help <cmd>`  →  Command details\n"
            f"📦 `{pfx}help <module>`  →  Plugin commands\n"
            f"📂 `{pfx}help <category>`  →  Category list\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ *Premium WhatsApp Automation*"
        )
        
        await smart_reply(message, txt)

    except Exception as e:
        import traceback
        logger.error(f"Help Error: {e}\n{traceback.format_exc()}")
        await smart_reply(message, f"❌ Help System Failure: `{e}`")
