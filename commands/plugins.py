from astra import Client, Message
from utils.plugin_utils import astra_command, COMMANDS_METADATA
from utils.helpers import edit_or_reply
from utils.ui_templates import UI
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

    output = (
        f"{UI.header('ASTRA PLUGIN MANIFEST')}\n"
        f"Plugins : {UI.mono(total_plugins)} modules\n"
        f"Registry: {UI.mono(total_cmds)} commands\n"
        f"{UI.DIVIDER}\n"
    )

    for cat in CATEGORY_ORDER:
        if cat not in categories:
            continue
        
        mods = sorted(list(categories[cat]))
        icon = get_label(cat)
        output += f"{UI.bold(icon)} {UI.bold(cat.upper())}\n"
        output += f"{UI.mono(', '.join(mods))}\n\n"

    # Other categories
    for cat in sorted(categories.keys()):
        if cat not in CATEGORY_ORDER:
            mods = sorted(list(categories[cat]))
            output += f"{UI.bold('[ OTH ]')} {UI.bold(cat.upper())}\n"
            output += f"{UI.mono(', '.join(mods))}\n\n"

    output += f"{UI.DIVIDER}\nUse {UI.mono('.help <plugin>')} for module details."
    await edit_or_reply(message, output)
