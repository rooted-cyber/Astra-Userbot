"""Group settings commands using the new Astra v3 API."""

import asyncio

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="lock",
    description="Restrict group actions to admins only.",
    category="Group Management",
    usage="<send|add|info|all> (e.g. .lock send)",
    owner_only=True,
)
async def lock_handler(client: Client, message: Message):
    """Locks a group setting to admins-only."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.bold('USAGE:')} {UI.mono('.lock <send|add|info|all>')}")

    target = args[0].lower()
    api = client.api
    gid = message.chat_id
    status = await edit_or_reply(message, f"{UI.mono('processing')} Restricting segment permissions...")

    try:
        if target in ("send", "all"):
            await api.set_admins_only_send(gid, True)
        if target in ("add", "all"):
            await api.set_admins_only_add(gid, True)
        if target in ("info", "all"):
            await api.set_admins_only_info(gid, True)

        label = target if target != "all" else "full segment"
        await status.edit(f"{UI.mono('done')} Persistent lock applied: {UI.mono(label)}")
    except Exception as e:
        await status.edit(f"{UI.mono('error')} Permission failure: {UI.mono(str(e))}")


@astra_command(
    name="unlock",
    description="Allow all members to perform group actions.",
    category="Group Management",
    usage="<send|add|info|all> (e.g. .unlock send)",
    owner_only=True,
)
async def unlock_handler(client: Client, message: Message):
    """Unlocks a group setting for all members."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.unlock <send|add|info|all>`")

    target = args[0].lower()
    api = client.api
    gid = message.chat_id
    status = await edit_or_reply(message, f"{UI.mono('processing')} syncing segment permissions...")

    try:
        if target in ("send", "all"):
            await api.set_admins_only_send(gid, False)
        if target in ("add", "all"):
            await api.set_admins_only_add(gid, False)
        if target in ("info", "all"):
            await api.set_admins_only_info(gid, False)

        label = target if target != "all" else "full segment"
        await status.edit(f"{UI.mono('done')} Permission shield removed: {UI.mono(label)}")
    except Exception as e:
        await status.edit(f"{UI.mono('error')} Synchronize failure: {UI.mono(str(e))}")


@astra_command(
    name="setsubject",
    description="Change group name.",
    category="Group Management",
    aliases=["setname", "gname"],
    usage="<new name>",
    owner_only=True,
)
async def setsubject_handler(client: Client, message: Message):
    """Changes the group subject/name."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.setsubject <new name>`")

    name = " ".join(args)
    try:
        await client.api.set_group_subject(message.chat_id, name)
        await edit_or_reply(message, f"{UI.mono('done')} Subject re-indexed: {UI.bold(name)}")
    except Exception as e:
        await edit_or_reply(message, f"{UI.mono('error')} Index failure: {UI.mono(str(e))}")


@astra_command(
    name="setdesc",
    description="Change group description.",
    category="Group Management",
    aliases=["gdesc", "setdescription"],
    usage="<new description>",
    owner_only=True,
)
async def setdesc_handler(client: Client, message: Message):
    """Changes the group description."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.setdesc <description>`")

    desc = " ".join(args)
    try:
        await client.api.set_group_description(message.chat_id, desc)
        await edit_or_reply(message, f"{UI.mono('done')} config updated.")
    except Exception as e:
        await edit_or_reply(message, f"{UI.mono('error')} config failure: {UI.mono(str(e))}")


@astra_command(
    name="joinreqs",
    description="View and approve/reject pending join requests.",
    category="Group Management",
    aliases=["requests", "pending"],
    usage="[approve|reject] (e.g. .joinreqs approve)",
    owner_only=True,
)
async def joinreqs_handler(client: Client, message: Message):
    """Manage group join requests."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    args = extract_args(message)
    api = client.api
    gid = message.chat_id

    try:
        reqs = await api.get_membership_requests(gid)
        if not reqs:
            return await edit_or_reply(message, f"{UI.mono('empty')} No pending nodes identified.")

        if not args:
            # Just list them
            text = f"{UI.header('PENDING NODES')}\n"
            for r in reqs[:20]:
                rid = r.get("id", "unknown").split("@")[0]
                text += f"• {UI.mono(rid)}\n"
            if len(reqs) > 20:
                text += f"\n{UI.italic(f'...and {len(reqs) - 20} more')}"
            text += f"\n\n{UI.bold('COMMANDS:')} {UI.mono('.joinreqs <approve|reject>')}"
            return await edit_or_reply(message, text)

        action = args[0].lower()
        status = await edit_or_reply(message, f"{UI.mono('processing')} Processing {len(reqs)} nodes...")

        if action == "approve":
            await api.approve_membership(gid)
            await status.edit(f"{UI.mono('done')} Approved {len(reqs)} access request(s).")
        elif action == "reject":
            await api.reject_membership(gid)
            await status.edit(f"{UI.mono('done')} Terminated {len(reqs)} access request(s).")
        else:
            await status.edit(f"{UI.mono('error')} Invalid operation parameter.")
    except Exception as e:
        await edit_or_reply(message, f"{UI.mono('error')} request failed: {UI.mono(str(e))}")


@astra_command(
    name="revoke",
    description="Revoke group invite link.",
    category="Group Management",
    usage="",
    owner_only=True,
)
async def revoke_handler(client: Client, message: Message):
    """Revokes and regenerates the group invite link."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "⚠️ Groups only.")

    try:
        new_link = await client.api.revoke_invite(message.chat_id)
        await edit_or_reply(message, f"{UI.mono('done')} Node link revoked.\nIdentifier: {new_link}")
    except Exception as e:
        await edit_or_reply(message, f"{UI.mono('error')} request failed: {UI.mono(str(e))}")
