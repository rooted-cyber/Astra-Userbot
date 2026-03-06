import logging
from config import config
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

logger = logging.getLogger("Astra.Help")

# ─────── Category Normalization Map ───────
CATEGORY_MAP = {
    # AI & Search
    "ai intelligence": "AI & Search",
    "duckduckgo": "AI & Search",
    "google": "AI & Search",
    # Tools & Utilities
    "astra essentials": "User & Account",
    "core tools": "Tools & Utilities",
    "utility": "Tools & Utilities",
    "general": "Tools & Utilities",
    "tools": "Tools & Utilities",
    "utility_cmds": "Tools & Utilities",
    # User / Account (New category for status/privacy/etc)
    "account": "Account & Privacy",
    "privacy": "Account & Privacy",
    "status": "User & Account",
    # Fun
    "fun": "Fun & Memes",
    "fun & games": "Fun & Memes",
    # Media
    "downloader": "Media & Downloads",
    "media engine": "Media & Downloads",
    "media": "Media & Downloads",
    "youtube": "Media & Downloads",
    "instagram": "Media & Downloads",
    # Image / Design (Merging Creative Suite)
    "creative suite": "Image & Design",
    "logo maker": "Image & Design",
    "image editor": "Image & Design",
    "image tools": "Image & Design",
    "video tools": "Image & Design",
    "audio tools": "Media & Downloads",
    # Group
    "group admin": "Group Management",
    "group management": "Group Management",
    # Owner
    "owner tools": "Owner & Sudo",
    "owner utility": "Owner & Sudo",
    "sudo": "Owner & Sudo",
    # System
    "system": "System & Bot",
    "system & bot": "System & Bot",
    "system hub": "System & Bot",
    "config": "System & Bot",
}

# Professional Technical Icons
CATEGORY_ICONS = {
    "AI & Search": "[ AI  ]",
    "User & Account": "[ USER ]",
    "Account & Privacy": "[ PVR  ]",
    "Tools & Utilities": "[ UTL  ]",
    "Fun & Memes": "[ FUN  ]",
    "Media & Downloads": "[ MED  ]",
    "Image & Design": "[ IMG  ]",
    "Group Management": "[ GRP  ]",
    "Owner & Sudo": "[ OWN  ]",
    "System & Bot": "[ SYS  ]",
}

CATEGORY_ORDER = [
    "AI & Search",
    "User & Account",
    "Account & Privacy",
    "Media & Downloads",
    "Image & Design",
    "Group Management",
    "Tools & Utilities",
    "Fun & Memes",
    "Owner & Sudo",
    "System & Bot",
]

def normalize_category(raw_cat: str) -> str:
    return CATEGORY_MAP.get(raw_cat.lower().strip(), raw_cat)

def get_label(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, "[ GEN ]")

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
    description="Access Astra command registry.",
    category="Tools & Utilities",
    usage="[cmd / cat / mod]",
    is_public=True,
)
async def help_handler(client: Client, message: Message):
    """Technical command registry with minimalist output."""
    try:
        from utils.state import state
        pfx = state.get_prefix()
        args = extract_args(message)
        _build_cache()
        merged = HELP_CACHE["merged"]
        by_mod = HELP_CACHE["by_module"]

        if args:
            q = args[0].lower().strip().lstrip(".!/")
            
            # Module search
            mod_match = by_mod.get(q)
            if mod_match:
                cmds = sorted(mod_match, key=lambda c: c["name"])
                txt = f"{UI.bold('PLUGIN REGISTRY:')} {UI.mono(q.upper())}\n{UI.DIVIDER}\n"
                for c in cmds:
                    txt += f" {UI.BULLET} {UI.mono(c['name'])}\n"
                txt += f"{UI.DIVIDER}\nTotal: {UI.mono(len(cmds))} commands\nUse {UI.mono(pfx + 'help <cmd>')} for usage."
                return await edit_or_reply(message, txt)

            # Category search
            full_query = " ".join(args).lower().strip()
            cat_match = next((c for c in merged if c.lower() == full_query or c.lower().replace(" ", "_") == q), None)
            if cat_match:
                cmds = sorted(merged[cat_match], key=lambda c: c["name"])
                txt = f"{UI.bold('CATEGORY:')} {UI.mono(cat_match.upper())}\n{UI.DIVIDER}\n"
                for c in cmds:
                    txt += f" {UI.BULLET} {UI.mono(c['name'])}\n"
                txt += f"{UI.DIVIDER}\nTotal: {UI.mono(len(cmds))} commands"
                return await edit_or_reply(message, txt)

            # Command search
            cmd = next((c for c in COMMANDS_METADATA if c["name"].lower() == q or q in [a.lower() for a in c.get("aliases", [])]), None)
            if cmd:
                txt = (
                    f"{UI.bold('COMMAND INFO')}\n{UI.DIVIDER}\n"
                    f"Command : {UI.mono(cmd['name'])}\n"
                    f"Info    : {UI.italic(cmd['description'])}\n"
                    f"Category: {UI.mono(normalize_category(cmd.get('category', '')))}\n"
                    f"Usage   : {UI.mono(f'{pfx}{cmd['name']} {cmd.get('usage', '')}')}\n"
                )
                if cmd.get("aliases"):
                    txt += f"Aliases : {UI.mono(', '.join(cmd['aliases']))}\n"
                txt += f"{UI.DIVIDER}\n{UI.italic(f'Astra Engine v{config.VERSION}')}"
                return await edit_or_reply(message, txt)

            return await edit_or_reply(message, f"{UI.mono(f'Error: Command {q} not found.')}")

        # Main Menu
        total_cmds = len(COMMANDS_METADATA)
        
        # Fetch Stats (Optional)
        total_usage = "N/A"
        try:
            from utils.database import db
            stats = await db.get_stats()
            total_usage = stats.get("sqlite", {}).get("state_records", "N/A") # Placeholder for actual usage count if tracked
            # Let's try to get a better total usage if available
            usage_data = await db.get("total_commands_v2", 0)
            total_usage = str(usage_data)
        except:
            pass

        txt = (
            f"{UI.bold('ASTRA COMMAND REGISTRY')}\n"
            f"{UI.DIVIDER}\n"
            f"Prefix  : {UI.mono(pfx)} | Total : {UI.mono(total_cmds)}\n"
            f"Usage   : {UI.mono(total_usage)} calls | State : {UI.mono('[ ACTIVE ]')}\n"
            f"{UI.DIVIDER}\n\n"
        )
        
        # Display ordered categories
        for cat in CATEGORY_ORDER:
            if cat not in merged: continue
            cmds = sorted(merged[cat], key=lambda c: c["name"])
            names = ", ".join([f"`{c['name']}`" for c in cmds])
            txt += f"{UI.bold(get_label(cat))} {UI.bold(cat.upper())} ({len(cmds)})\n{names}\n\n"

        # Any uncategorized leftovers
        for cat in sorted(merged.keys()):
            if cat not in CATEGORY_ORDER:
                cmds = sorted(merged[cat], key=lambda c: c["name"])
                names = ", ".join([f"`{c['name']}`" for c in cmds])
                txt += f"{UI.bold('[ OTH ]')} {UI.bold(cat.upper())} ({len(cmds)})\n{names}\n\n"

        txt += (
            f"{UI.DIVIDER}\n"
            f"💡 {UI.mono(pfx + 'help <cmd>')}  ➜  Details\n"
            f"📦 {UI.mono(pfx + 'help <mod>')}  ➜  Plugin\n"
            f"📂 {UI.mono(pfx + 'help <cat>')}  ➜  Category\n"
            f"{UI.DIVIDER}\n"
            f"{UI.italic('Manual: github.com/paman7647/Astra')}"
        )
        await edit_or_reply(message, txt)

    except Exception as e:
        logger.error(f"Help Error: {e}", exc_info=True)
        await edit_or_reply(message, f"{UI.mono(f'System Failure: {e}')}")
