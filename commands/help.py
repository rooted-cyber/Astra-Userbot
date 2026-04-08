import logging
import time

from config import config
from . import *
from utils.helpers import edit_or_reply

logger = logging.getLogger("Astra.Help")

LINE = "───"

CATEGORY_DATA = {
    "AI & Search": {"desc": "search and language tools"},
    "User & Account": {"desc": "profile and account controls"},
    "Media & Downloads": {"desc": "media fetch and download commands"},
    "Image & Design": {"desc": "image editing and design tools"},
    "Group Management": {"desc": "group administration commands"},
    "Tools & Utilities": {"desc": "general utility commands"},
    "Fun & Memes": {"desc": "fun and social commands"},
    "Owner & Sudo": {"desc": "owner-only and sudo actions"},
    "System & Bot": {"desc": "system status and maintenance"},
}

CATEGORY_MAP = {
    "ai & search": "AI & Search",
    "ai": "AI & Search",
    "search": "AI & Search",

    "user": "User & Account",
    "account": "User & Account",
    "privacy": "User & Account",

    "tools": "Tools & Utilities",
    "tools & utilities": "Tools & Utilities",
    "utility": "Tools & Utilities",
    "general": "Tools & Utilities",

    "media": "Media & Downloads",
    "media & downloads": "Media & Downloads",
    "downloader": "Media & Downloads",

    "group": "Group Management",
    "group management": "Group Management",

    "owner": "Owner & Sudo",
    "owner & sudo": "Owner & Sudo",
    "sudo": "Owner & Sudo",

    "system": "System & Bot",
    "system & bot": "System & Bot",
    "config": "System & Bot",
    "status": "System & Bot",

    "fun": "Fun & Memes",
    "fun & memes": "Fun & Memes",

    "creative suite": "Image & Design",
    "image": "Image & Design",
    "design": "Image & Design",
}

CATEGORY_ORDER = list(CATEGORY_DATA.keys())

# Unique short names for opening categories directly.
CATEGORY_SHORTCUTS = {
    "AI & Search": "ai",
    "User & Account": "usr",
    "Media & Downloads": "med",
    "Image & Design": "img",
    "Group Management": "grp",
    "Tools & Utilities": "utl",
    "Fun & Memes": "fun",
    "Owner & Sudo": "own",
    "System & Bot": "sys",
}


def get_label(cat: str) -> str:
    return "•"


def normalize_category(raw_cat: str) -> str:
    if not raw_cat:
        return "Tools & Utilities"
    return CATEGORY_MAP.get(raw_cat.lower().strip(), raw_cat)


def _build_category_lookup() -> dict:
    lookup = {}
    for category in CATEGORY_ORDER:
        key = category.lower().strip()
        lookup[key] = category
        lookup[key.replace(" & ", " and ")] = category
        lookup[key.replace(" & ", "_")] = category
        lookup[key.replace(" ", "_")] = category

        short = CATEGORY_SHORTCUTS.get(category)
        if short:
            lookup[short] = category

    # Common alternate names that should still open canonical categories.
    alias_map = {
        "tools": "Tools & Utilities",
        "utility": "Tools & Utilities",
        "media": "Media & Downloads",
        "downloader": "Media & Downloads",
        "group": "Group Management",
        "owner": "Owner & Sudo",
        "sudo": "Owner & Sudo",
        "system": "System & Bot",
        "config": "System & Bot",
        "status": "System & Bot",
        "creative": "Image & Design",
        "creative_suite": "Image & Design",
        "image": "Image & Design",
        "design": "Image & Design",
        "fun": "Fun & Memes",
        "ai": "AI & Search",
        "account": "User & Account",
        "user": "User & Account",
    }
    lookup.update(alias_map)
    return lookup


HELP_CACHE = {"merged": {}, "built": False}
_HELP_SEEN = {}


def _mark_help_seen(message_id: str) -> bool:
    now = time.time()
    stale = [k for k, ts in _HELP_SEEN.items() if now - ts > 30]
    for key in stale:
        _HELP_SEEN.pop(key, None)

    if message_id in _HELP_SEEN:
        return False

    _HELP_SEEN[message_id] = now
    return True


def _unique_commands_by_name():
    """Return deduplicated command entries keyed by command name."""
    unique = {}
    for cmd in COMMANDS_METADATA:
        name = str(cmd.get("name", "")).strip().lower()
        if not name:
            continue
        unique[name] = cmd
    return list(unique.values())


def _build_cache() -> None:
    HELP_CACHE["merged"].clear()
    for cmd in _unique_commands_by_name():
        category = normalize_category(cmd.get("category", "Tools & Utilities"))
        if category not in CATEGORY_DATA:
            category = "Tools & Utilities"
        HELP_CACHE["merged"].setdefault(category, []).append(cmd)

    for cat in HELP_CACHE["merged"]:
        HELP_CACHE["merged"][cat] = sorted(HELP_CACHE["merged"][cat], key=lambda c: c["name"])

    HELP_CACHE["built"] = True


@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="show help menu",
    category="Tools & Utilities",
    usage="[command/category]",
    is_public=True,
)
async def help_handler(client: Client, message: Message):
    msg_id = str(getattr(message, "id", ""))
    if msg_id and not _mark_help_seen(msg_id):
        return

    try:
        from utils.state import state

        pfx = state.get_prefix()
        args = extract_args(message)
        _build_cache()
        merged = HELP_CACHE["merged"]
        unique_commands = _unique_commands_by_name()
        category_lookup = _build_category_lookup()

        if args:
            key = " ".join(args).lower().strip().lstrip(".!/")

            # Exact category keys and shortnames take priority over command aliases.
            cat_match = category_lookup.get(key)
            if cat_match and cat_match in merged:
                cmds = merged[cat_match]
                txt = (
                    f"**category**\n{LINE}\n"
                    f"name: `{cat_match}`\n"
                    f"short: `{CATEGORY_SHORTCUTS.get(cat_match, '-')}`\n"
                    f"info: {CATEGORY_DATA.get(cat_match, {}).get('desc', 'command group')}\n"
                    f"count: `{len(cmds)}`\n"
                    f"{LINE}\n"
                )
                for item in cmds:
                    txt += f"`{item['name']}`  {item.get('description', '')}\n"
                return await edit_or_reply(message, txt)

            cmd_matches = [
                c
                for c in unique_commands
                if c["name"].lower() == key
                or key in [a.lower() for a in c.get("aliases", [])]
            ]
            if len(cmd_matches) > 1:
                names = ", ".join(sorted(c["name"] for c in cmd_matches))
                return await edit_or_reply(
                    message,
                    f"ambiguous alias: `{key}`\n{LINE}\nmatches: `{names}`\nuse exact command name",
                )

            if cmd_matches:
                cmd = cmd_matches[0]
                usage = cmd.get("usage", "").strip()
                use_line = f"{pfx}{cmd['name']} {usage}".strip()
                txt = (
                    f"**command**\n{LINE}\n"
                    f"name: `{cmd['name']}`\n"
                    f"category: `{normalize_category(cmd.get('category', ''))}`\n"
                    f"info: {cmd.get('description', 'n/a')}\n"
                    f"usage: `{use_line}`\n"
                )
                if cmd.get("aliases"):
                    txt += f"aliases: `{', '.join(cmd['aliases'])}`\n"
                txt += f"{LINE}\nversion: `{config.VERSION}`"
                return await edit_or_reply(message, txt)

            return await edit_or_reply(message, f"not found: {key}")

        total_cmds = len(unique_commands)
        total_usage = "N/A"
        try:
            from utils.database import db

            total_usage = str(await db.get("total_commands_v2", 0))
        except Exception:
            pass

        txt = (
            "**Astra Userbot Menu**\n"
            f"{LINE}\n"
            f"prefix {pfx}   version {config.VERSION}\n"
            f"commands {total_cmds}   usage {total_usage}\n"
            "status online\n"
            f"{LINE}\n"
        )

        for cat in CATEGORY_ORDER:
            if cat not in merged:
                continue
            desc = CATEGORY_DATA.get(cat, {}).get("desc", "tools")
            count = len(merged.get(cat, []))
            short = CATEGORY_SHORTCUTS.get(cat, "-")
            txt += (
                f"[{short}] {cat} ({count})\n"
                f"  {desc}\n"
            )

        txt += (
            f"{LINE}\n"
            "open\n"
            f"- {pfx}help <shortname>\n"
            f"- {pfx}help <category>\n"
            f"- {pfx}help <command>\n"
            f"examples: {pfx}help sys, {pfx}help med, {pfx}help ping"
        )
        await edit_or_reply(message, txt)

    except Exception as e:
        logger.error(f"Help Error: {e}", exc_info=True)
        await edit_or_reply(message, f"error: {e}")
