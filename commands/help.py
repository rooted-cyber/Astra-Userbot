import logging
from config import config
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

logger = logging.getLogger("Astra.Help")

# ─────── Category Intelligence Map ───────
CATEGORY_DATA = {
    "AI & Search": {
        "desc": "Smart explorers and AI models.",
        "keywords": ["ai", "google", "wiki", "define"],
        "icon": "✧"
    },
    "User & Account": {
        "desc": "Manage your profile and presence.",
        "keywords": ["status", "privacy", "bio", "name"],
        "icon": "👤"
    },
    "Media & Downloads": {
        "desc": "Grab media from social platforms.",
        "keywords": ["instagram", "youtube", "reddit", "song"],
        "icon": "⬇"
    },
    "Image & Design": {
        "desc": "Create logos and edit photos.",
        "keywords": ["logo", "txtimg", "rmbg", "blur"],
        "icon": "🎨"
    },
    "Group Management": {
        "desc": "Tools for group synchronization.",
        "keywords": ["tagall", "purge", "admin", "mute"],
        "icon": "👥"
    },
    "Tools & Utilities": {
        "desc": "Essential bots and micro-tools.",
        "keywords": ["calc", "weather", "tr", "id"],
        "icon": "🛠"
    },
    "Fun & Memes": {
        "desc": "Boredom killers and meme makers.",
        "keywords": ["meme", "joke", "hack", "fake"],
        "icon": "🎭"
    },
    "Owner & Sudo": {
        "desc": "Restricted administrative controls.",
        "keywords": ["sudo", "install", "pmpermit", "run"],
        "icon": "🔑"
    },
    "System & Bot": {
        "desc": "Core heart and engine metrics.",
        "keywords": ["ping", "restart", "stats", "update"],
        "icon": "⚙"
    }
}

# Category Normalization Map
CATEGORY_MAP = {
    "ai intelligence": "AI & Search",
    "duckduckgo": "AI & Search",
    "google": "AI & Search",
    "astra essentials": "User & Account",
    "core tools": "Tools & Utilities",
    "utility": "Tools & Utilities",
    "general": "Tools & Utilities",
    "tools": "Tools & Utilities",
    "utility_cmds": "Tools & Utilities",
    "account": "Account & Privacy",
    "privacy": "Account & Privacy",
    "status": "User & Account",
    "fun": "Fun & Memes",
    "fun & games": "Fun & Memes",
    "downloader": "Media & Downloads",
    "media engine": "Media & Downloads",
    "media": "Media & Downloads",
    "youtube": "Media & Downloads",
    "instagram": "Media & Downloads",
    "creative suite": "Image & Design",
    "logo maker": "Image & Design",
    "image editor": "Image & Design",
    "image tools": "Image & Design",
    "video tools": "Image & Design",
    "audio tools": "Media & Downloads",
    "group admin": "Group Management",
    "group management": "Group Management",
    "owner tools": "Owner & Sudo",
    "owner utility": "Owner & Sudo",
    "sudo": "Owner & Sudo",
    "system": "System & Bot",
    "system & bot": "System & Bot",
    "system hub": "System & Bot",
    "config": "System & Bot",
}

CATEGORY_ORDER = list(CATEGORY_DATA.keys())

def normalize_category(raw_cat: str) -> str:
    return CATEGORY_MAP.get(raw_cat.lower().strip(), raw_cat)

HELP_CACHE = {
    "merged": {},
    "by_module": {},
    "built": False,
}

def _build_cache():
    HELP_CACHE["merged"].clear()
    HELP_CACHE["by_module"].clear()
    for cmd in COMMANDS_METADATA:
        ucat = normalize_category(cmd.get("category", "Tools & Utilities"))
        HELP_CACHE["merged"].setdefault(ucat, []).append(cmd)
        mod = cmd.get("module", "unknown")
        HELP_CACHE["by_module"].setdefault(mod, []).append(cmd)
    HELP_CACHE["built"] = True

@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="Explore the Astra command ecosystem.",
    category="Tools & Utilities",
    usage="[term / category]",
    is_public=True,
)
async def help_handler(client: Client, message: Message):
    """Modernized dashboard for Astra discovery."""
    try:
        from utils.state import state
        pfx = state.get_prefix()
        args = extract_args(message)
        _build_cache()
        merged = HELP_CACHE["merged"]

        # ─── CASE 1: SPECIFIC SEARCH ───
        if args:
            q = " ".join(args).lower().strip().lstrip(".!/")
            
            # 1. Match Command
            cmd = next((c for c in COMMANDS_METADATA if c["name"].lower() == q or q in [a.lower() for a in c.get("aliases", [])]), None)
            if cmd:
                txt = (
                    f"{UI.bold('✺ DISCOVERY')} : {UI.mono(cmd['name'].upper())}\n"
                    f"{UI.DIVIDER}\n"
                    f" ➜ {UI.bold('Description')}: {UI.italic(cmd['description'])}\n"
                    f" ➜ {UI.bold('Category')}   : {UI.mono(normalize_category(cmd.get('category', '')))}\n"
                    f" ➜ {UI.bold('Syntax')}     : {UI.mono(f'{pfx}{cmd['name']} {cmd.get('usage', '')}')}\n"
                )
                if cmd.get("aliases"):
                    txt += f" ➜ {UI.bold('Shortcuts')}  : {UI.mono(', '.join(cmd['aliases']))}\n"
                txt += f"\n{UI.italic(f'Astra Engine v{config.VERSION}')}"
                return await edit_or_reply(message, txt)

            # 2. Match Category
            cat_match = next((c for c in merged if c.lower() == q or c.lower().replace(" ", "_") == q or q in c.lower()), None)
            if cat_match:
                cmds = sorted(merged[cat_match], key=lambda c: c["name"])
                txt = f"{UI.bold('📂 EXPLORING')} : {UI.mono(cat_match.upper())}\n{UI.DIVIDER}\n"
                txt += f"{UI.italic(CATEGORY_DATA.get(cat_match, {}).get('desc', 'Collection of modules.'))}\n\n"
                
                # Formatted grid
                for i in range(0, len(cmds), 3):
                    row = cmds[i:i+3]
                    txt += "  " + "  ".join([UI.mono(c['name']) for c in row]) + "\n"
                
                txt += f"\n{UI.DIVIDER}\nTotal : {UI.mono(len(cmds))} commands available."
                return await edit_or_reply(message, txt)

            return await edit_or_reply(message, f"{UI.FAILURE} {UI.mono(f'Unknown query: {q}')}")

        # ─── CASE 2: DASHBOARD MAIN MENU ───
        total_cmds = len(COMMANDS_METADATA)
        
        # Stats Aggregation
        total_usage = "N/A"
        try:
            from utils.database import db
            total_usage = str(await db.get("total_commands_v2", 0))
        except: pass

        # Header Box
        txt = (
            f"{UI.BOX_TOP}\n"
            f"  {UI.bold('ASTRA EXPLORER DASHBOARD')}\n"
            f"  {UI.DIVIDER_THIN}\n"
            f"  {UI.LABEL_PFX} : {UI.mono(pfx)}\n"
            f"  {UI.LABEL_CMD} : {UI.mono(total_cmds)}\n"
            f"  {UI.LABEL_USE} : {UI.mono(total_usage)}\n"
            f"  {UI.STATUS_ACTIVE}\n"
            f"{UI.BOX_BOTTOM}\n\n"
        )
        
        txt += f"{UI.bold('CHOOSE A SECTOR TO EXPLORE')}\n\n"
        
        for cat in CATEGORY_ORDER:
            if cat not in merged: continue
            data = CATEGORY_DATA.get(cat, {})
            icon = data.get("icon", "•")
            desc = data.get("desc", "Various tools.")
            sample = ", ".join(data.get("keywords", []))
            
            txt += (
                f"{UI.bold(icon)} {UI.bold(cat.upper())}\n"
                f" {UI.italic(desc)}\n"
                f" {UI.mono(sample + '...')}\n\n"
            )

        # Catch-all
        for cat in sorted(merged.keys()):
            if cat not in CATEGORY_ORDER:
                cmds = sorted(merged[cat], key=lambda c: c["name"])
                txt += f"{UI.bold('•')} {UI.bold(cat.upper())} ({len(cmds)})\n\n"

        txt += (
            f"{UI.DIVIDER}\n"
            f"💡 {UI.bold('PRO TIP')}: Use {UI.mono(pfx + 'help <category>')} to see all commands in a sector. (e.g. {UI.mono(pfx + 'help Media')})\n\n"
            f"⎆ {UI.bold('GITHUB')}: github.com/paman7647/Astra-Userbot"
        )
        await edit_or_reply(message, txt)

    except Exception as e:
        logger.error(f"Help Dashboard Error: {e}", exc_info=True)
        await edit_or_reply(message, f"{UI.FAILURE} {UI.mono(f'Engine Error: {e}')}")
