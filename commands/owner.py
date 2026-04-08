"""
Owner Commands: Profile and Account Management
--------------------------------------------
Commands to update profile info, bio, pfp, and status stories.
"""

import base64
import os
import re
import time

from utils.bridge_downloader import bridge_downloader

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


def _normalize_plugin_module_name(filename: str) -> str:
    """Return a safe python module name for plugins."""
    base = os.path.basename(filename or "")
    stem = os.path.splitext(base)[0].strip().lower()
    stem = re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")

    # Avoid low-signal and collision-prone generic names.
    blocked = {
        "",
        "plugin",
        "plugins",
        "help",
        "owner",
        "__init__",
    }
    if not stem or stem in blocked:
        stem = f"ext_{int(time.time())}"

    if stem[0].isdigit():
        stem = f"ext_{stem}"

    return stem


@astra_command(
    name="setname",
    description="Update your profile display name.",
    category="Owner",
    usage="<new_name> (e.g. John Doe)",
    owner_only=True,
)
async def setname_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.mono('error')} New display identifier required.")

    new_name = " ".join(args)
    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Re-indexing profile name...")

    try:
        await client.account.set_name(new_name)
        await status_msg.edit(f"{UI.mono('done')} Profile identifier synced: {UI.bold(new_name)}")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} sync failed: {UI.mono(str(e))}")


@astra_command(
    name="bio",
    description="Update your profile 'About' (Bio) text.",
    category="Owner",
    aliases=["setbio", "setabout"],
    usage="<text> (e.g. Available)",
    owner_only=True,
)
async def setbio_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.mono('error')} New config entry required.")

    new_bio = " ".join(args)
    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Updating profile config...")

    try:
        await client.account.set_about_text(new_bio)
        await status_msg.edit(f"{UI.mono('done')} Profile config updated.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Update failure: {UI.mono(str(e))}")


@astra_command(
    name="setpfp",
    description="Update your profile picture.",
    category="Owner",
    usage="(reply to image) (e.g. .setpfp reply)",
    owner_only=True,
)
async def setpfp_handler(client: Client, message: Message):
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, f"{UI.mono('error')} Target image buffer required.")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Rendering profile asset...")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('error')} Asset extraction failed.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")

        # Call API method
        success = await client.account.update_profile_pic(media_b64)

        if success:
            await status_msg.edit(f"{UI.mono('done')} Profile asset synced.")
        else:
            await status_msg.edit(f"{UI.mono('error')} Profile update rejected by protocol.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} request failed: {UI.mono(str(e))}")


@astra_command(
    name="setgpic",
    description="Update the current group's picture.",
    category="Owner",
    aliases=["setgrouppfp"],
    usage="(reply to image) (e.g. .setgpic reply)",
    owner_only=True,
)
async def setgpic_handler(client: Client, message: Message):
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, f"{UI.mono('error')} Target workspace out of bounds (Group only).")
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, f"{UI.mono('error')} Target image buffer required.")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Rendering group asset...")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('error')} Asset extraction failed.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")
        success = await client.group.update_profile_pic(message.chat_id, media_b64)

        if success:
            await status_msg.edit(f"{UI.mono('done')} Group asset synced.")
        else:
            await status_msg.edit(f"{UI.mono('error')} Group update rejected by protocol.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} request failed: {UI.mono(str(e))}")


@astra_command(
    name="privacy",
    description="View or update your privacy settings.",
    category="Owner",
    usage="[category value] (e.g. last_seen all)",
    owner_only=True,
)
async def privacy_handler(client: Client, message: Message):
    args = extract_args(message)

    if not args:
        status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Fetching privacy config...")
        try:
            settings = await client.account.get_settings()
            text = f"{UI.header('PRIVACY MANIFEST')}\n"
            for k, v in settings.items():
                text += f"• {UI.bold(k.replace('_', ' ').title())}: {UI.mono(v)}\n"
            text += f"\n{UI.italic('Set via .privacy <category> <value>')}\n{UI.mono('Scope: last_seen, profile_pic, about, status, read_receipts')}"
            await status_msg.edit(text)
        except Exception as e:
            await status_msg.edit(f"{UI.mono('error')} config retrieval failure: {UI.mono(str(e))}")
        return

    if len(args) < 2:
        return await edit_or_reply(
            message,
            " ⚠️ Usage: `.privacy <category> <value>`\nCategories: last_seen, profile_pic, about, status, read_receipts\nValues: all, contacts, none",
        )

    category = args[0].lower()
    value = args[1].lower()

    # Map read_receipts bool
    if category == "read_receipts":
        value = value in ["true", "on", "yes", "enabled", "all"]

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} syncing {UI.mono(category)} scope...")

    try:
        method_map = {
            "last_seen": client.account.set_last_seen,
            "profile_pic": client.account.set_profile_pic,
            "about": client.account.set_about,
            "status": client.account.set_status,
            "read_receipts": client.account.set_read_receipts,
        }

        if category not in method_map:
            return await status_msg.edit(f"{UI.mono('error')} Invalid security scope: {UI.mono(category)}")

        await method_map[category](value)
        await status_msg.edit(f"{UI.mono('done')} {UI.mono(category)} scope synced to {UI.bold(str(value))}.")
    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} sync failed: {UI.mono(str(e))}")


@astra_command(
    name="install",
    description="Install a new plugin by replying to a .py file.",
    category="Owner",
    usage="(reply to .py file)",
    owner_only=True,
)
async def install_handler(client: Client, message: Message):
    args = extract_args(message)
    force = "-f" in args or "--force" in args

    if not message.has_quoted_msg:
        return await edit_or_reply(message, f"{UI.mono('error')} Target plugin buffer (.py) required.")

    quoted = message.quoted
    filename = getattr(quoted, "filename", None) or "ext_plugin.py"

    if not filename.endswith(".py"):
        return await edit_or_reply(message, f"{UI.mono('error')} Invalid asset format. Only .py files are allowed.")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Extracting plugin payload: {UI.mono(filename)}...")

    try:
        # Use high-reliability bridge downloader
        from utils.bridge_downloader import bridge_downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('error')} Payload extraction failure.")

        module_name = _normalize_plugin_module_name(filename)
        clean_name = f"{module_name}.py"
        target_dir = os.path.join(os.getcwd(), "commands")
        target_path = os.path.join(target_dir, clean_name)

        # Block collisions unless explicitly forced.
        if os.path.exists(target_path) and not force:
            return await status_msg.edit(
                f"{UI.mono('error')} Scope {UI.mono(module_name)} already exists. Use .install -f to overwrite."
            )

        # Validate syntax before writing to disk.
        source_text = media_data.decode("utf-8", errors="replace")
        try:
            compile(source_text, clean_name, "exec")
        except Exception as syn_err:
            return await status_msg.edit(
                f"{UI.mono('error')} Syntax check failed: {UI.mono(str(syn_err))}"
            )

        backup_data = None
        existed_before = os.path.exists(target_path)
        if existed_before:
            with open(target_path, "rb") as f:
                backup_data = f.read()

        # Write the downloaded data to the target path
        with open(target_path, "wb") as f:
            f.write(media_data)

        # Load the plugin
        from utils.plugin_utils import load_plugin
        if load_plugin(client, f"commands.{module_name}"):
            await status_msg.edit(
                f"{UI.header('PLUGIN INSTALLED')}\n"
                f"• Asset: {UI.mono(clean_name)}\n"
                f"• Scope: {UI.mono('commands.' + module_name)}\n"
                f"• Status: {UI.bold('ACTIVE')}\n\n"
                f"{UI.italic('Plugin is now persistent and live.')}"
            )
        else:
            # Roll back filesystem state when dynamic load fails.
            if existed_before and backup_data is not None:
                with open(target_path, "wb") as f:
                    f.write(backup_data)
            elif os.path.exists(target_path):
                os.remove(target_path)
            await status_msg.edit(f"{UI.mono('error')} Dynamic loading failed. Check logs for syntax issues.")

    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Installation reached a critical failure: {UI.mono(str(e))}")


@astra_command(
    name="uninstall",
    description="Remove a plugin and delete its file.",
    category="Owner",
    usage="<plugin_name> (e.g. .uninstall my_plugin)",
    owner_only=True,
)
async def uninstall_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.mono('error')} Plugin identifier required.")

    plugin_name = _normalize_plugin_module_name(args[0].replace(".py", ""))
    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Purging plugin scope: {UI.mono(plugin_name)}...")

    try:
        import os
        from utils.plugin_utils import unload_plugin

        target_path = os.path.join(os.getcwd(), "commands", f"{plugin_name}.py")

        # 1. Unload from memory
        unload_plugin(client, f"commands.{plugin_name}")

        # 2. Remove from disk
        if os.path.exists(target_path):
            os.remove(target_path)
            await status_msg.edit(f"{UI.mono('done')} Plugin {UI.mono(plugin_name)} purged from disk and memory.")
        else:
            await status_msg.edit(f"{UI.mono('error')} Scope {UI.mono(plugin_name)} not found on disk.")

    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Purge failed: {UI.mono(str(e))}")
