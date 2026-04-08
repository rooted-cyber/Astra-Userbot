from utils.state import state

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="pmpermit",
    description="Toggle PM Protection or permit/deny users",
    category="Owner",
    aliases=[],
    usage="<on|off|approve|deny> [user_id] (e.g. .pmpermit approve @123)",
    owner_only=True,
)
async def pmpermit_handler(client: Client, message: Message):
    """Toggle PM Protection or permit/deny users"""
    args_list = extract_args(message)

    if not args_list:
        status = f"{UI.mono('enabled')} Shielded" if state.get_config("ENABLE_PM_PROTECTION") else f"{UI.mono('disabled')} Open"
        permitted_count = len(state.state.get("pm_permits", []))

        help_text = (
            f"{UI.header('PM SECURITY PROTOCOL')}\n"
            f"Status : {status}\n"
            f"Nodes  : {UI.mono(permitted_count)} Trusted\n"
            f"Limit  : {UI.mono(state.get_config('PM_WARN_LIMIT'))} Warnings\n\n"
            f"{UI.bold('OPERATIONS:')}\n"
            f"• {UI.mono('.pmpermit <on|off>')} - Toggle Shield\n"
            f"• {UI.mono('.pmpermit approve')} - Authorize User\n"
            f"• {UI.mono('.pmpermit deny ')} - Revoke Access\n"
            f"• {UI.mono('.pmpermit list ')} - List Trusted Nodes"
        )
        return await edit_or_reply(message, help_text)

    action = args_list[0].lower()

    if action == "on":
        state.set_config("ENABLE_PM_PROTECTION", True)
        await edit_or_reply(message, f"{UI.mono('done')} PM Security Shield enabled.")
    elif action == "off":
        state.set_config("ENABLE_PM_PROTECTION", False)
        await edit_or_reply(message, f"{UI.mono('done')} PM Security Shield disabled.")
    elif action in ["approve", "permit", "a"]:
        target_id = None
        if len(args_list) > 1:
            target_id = args_list[1]
        elif message.has_quoted_msg:
            quoted = message.quoted
            target_id = quoted.sender or quoted.chat_id
        elif not str(message.chat_id).endswith("@g.us"):
            target_id = message.chat_id

        if not target_id:
            return await edit_or_reply(
                message, f"{UI.mono('error')} Target identification required."
            )

        # Handle JID objects or strings
        target_str = target_id.serialized if hasattr(target_id, "serialized") else str(target_id)
        if "@" not in target_str:
            target_str = f"{target_str}@c.us"

        # Normalization: Ensure we only store primary JID (stripping :x)
        if ":" in target_str.split("@", 1)[0]:
            target_str = target_str.split(":", 1)[0] + "@" + target_str.split("@", 1)[1]

        state.permit_user(target_str)
        name = await get_contact_name(client, target_str)
        await edit_or_reply(message, f"{UI.mono('done')} {UI.mono(name)} authorized via Security Protocol.")

    elif action in ["deny", "d"]:
        target_id = None
        if len(args_list) > 1:
            target_id = args_list[1]
        elif message.has_quoted_msg:
            quoted = message.quoted
            target_id = quoted.sender or quoted.chat_id
        elif not str(message.chat_id).endswith("@g.us"):
            target_id = message.chat_id

        if not target_id:
            return await edit_or_reply(
                message, f"{UI.mono('error')} Target identification required."
            )

        # Handle JID objects or strings
        target_str = target_id.serialized if hasattr(target_id, "serialized") else str(target_id)
        if "@" not in target_str:
            target_str = f"{target_str}@c.us"

        state.deny_user(target_str)
        name = await get_contact_name(client, target_str)
        await edit_or_reply(message, f"{UI.mono('done')} {UI.mono(name)} access revoked.")
    elif action == "list":
        permitted = state.state.get("pm_permits", [])
        if not permitted:
            return await edit_or_reply(message, f"{UI.mono('empty')} No trusted nodes identified.")

        list_text = f"{UI.header('TRUSTED NODES')}\n"
        for i, uid in enumerate(permitted, 1):
            name = await get_contact_name(client, uid)
            list_text += f"{i}. {UI.bold(name)} ({UI.mono(uid.split('@')[0])})\n"

        await edit_or_reply(message, list_text)

    else:
        await edit_or_reply(message, f"{UI.mono('error')} Invalid operation: {UI.mono(action)}")
