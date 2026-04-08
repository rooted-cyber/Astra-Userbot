from astra import Client, Message
from utils.plugin_utils import astra_command, COMMANDS_METADATA
from utils.helpers import edit_or_reply
from commands.help import normalize_category, get_label, CATEGORY_ORDER

@astra_command(
    name="plugins",
    description="List all loaded plugin modules and command counts.",
    category="System & Bot",
    aliases=["pl", "modules"],
    is_public=True,
)
async def plugins_list_handler(client: Client, message: Message):
    """Displays a list of all loaded plugins and their command density."""
    
    # Organize by category
    categories = {}
    for cmd in COMMANDS_METADATA:
        cat = normalize_category(cmd.get("category", "Tools & Utilities"))
        categories.setdefault(cat, set()).add(cmd.get("module", "unknown"))

    total_cmds = len(COMMANDS_METADATA)
    total_plugins = len(set(cmd.get("module", "unknown") for cmd in COMMANDS_METADATA))

    line = "───"
    output = (
        f"**plugin config**\n"
        f"{line}\n"
        f"modules: `{total_plugins}`\n"
        f"commands: `{total_cmds}`\n"
        f"{line}\n"
    )

    for cat in CATEGORY_ORDER:
        if cat not in categories:
            continue
        
        mods = sorted(list(categories[cat]))
        output += f"{cat}\n"
        output += f"{', '.join(mods)}\n"

    # Other categories
    for cat in sorted(categories.keys()):
        if cat not in CATEGORY_ORDER:
            mods = sorted(list(categories[cat]))
            output += f"{cat}\n"
            output += f"{', '.join(mods)}\n"

    output += f"{line}\nusage: `.help <command>`"
    await edit_or_reply(message, output)
