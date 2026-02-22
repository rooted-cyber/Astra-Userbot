# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import sys
import asyncio
import time
import hashlib
from . import *

@astra_command(
    name="restart",
    description="Restarts the bot process",
    category="Owner Utility",
    owner_only=True
)
async def restart_cmd(client: Client, message: Message):
    """Restarts the bot process"""
    await smart_reply(message, "🚀 *Restarting Astra Userbot...*")
    # Restart the application
    os.execv(sys.executable, [sys.executable] + sys.argv)

@astra_command(
    name="shutdown",
    description="Shuts down the bot process",
    category="Owner Utility",
    owner_only=True
)
async def shutdown_cmd(client: Client, message: Message):
    """Shuts down the bot process"""
    await smart_reply(message, "🛑 *Shutting down Astra Userbot...*")
    # Exit the application
    sys.exit(0)

@astra_command(
    name="update",
    description="Updates the bot from GitHub.",
    category="Owner Utility",
    owner_only=True,
    usage=".update [-b branch] [-f]"
)
async def update_cmd(client: Client, message: Message):
    """
    Advanced Update Orchestrator:
    - Supports branch selection (-b). Default: master.
    - Force update (-f)
    - Already up-to-date detection
    - Change log / Diff summary
    - Automatic requirements installation
    - Restart upon success
    """
    args = extract_args(message)
    force = "-f" in args
    
    # Parse branch (Default to master as requested)
    branch = "master"
    if "-b" in args:
        idx = args.index("-b")
        if len(args) > idx + 1:
            branch = args[idx + 1]
    
    status_msg = await smart_reply(message, f"📡 *Astra Update Engine:* Syncing with `{branch}`...")
    
    try:
        # Check for Git
        if not os.path.exists(".git"):
            return await status_msg.edit("❌ *Error:* Directory is not a git repository.")

        # 1. Fetch latest from remote
        await status_msg.edit(f"📥 *Fetching updates for branch:* `{branch}`...")
        proc = await asyncio.create_subprocess_exec(
            'git', 'fetch', 'origin', branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        
        if proc.returncode != 0:
            return await status_msg.edit(f"❌ *Fetch failed:* Ensure the branch `{branch}` exists on remote.")

        # 2. Compare versions
        proc_local = await asyncio.create_subprocess_exec('git', 'rev-parse', 'HEAD', stdout=asyncio.subprocess.PIPE)
        local_hash_raw, _ = await proc_local.communicate()
        
        proc_remote = await asyncio.create_subprocess_exec('git', 'rev-parse', f'origin/{branch}', stdout=asyncio.subprocess.PIPE)
        remote_hash_raw, _ = await proc_remote.communicate()
        
        local_hash = local_hash_raw.decode().strip()
        remote_hash = remote_hash_raw.decode().strip()

        if local_hash == remote_hash and not force:
            await asyncio.sleep(0.5)
            return await status_msg.edit(
                f"✅ **Astra is already up to date.**\n"
                f"Branch: `{branch}`\n"
                f"Version: `{config.VERSION}` - **{config.VERSION_NAME}** (`{local_hash[:7]}`)\n\n"
                f"💡 Use `.update -f` to force a reset if you've made local changes."
            )

        # 3. Handle Diff if not forced
        if local_hash != remote_hash and not force:
            proc_diff = await asyncio.create_subprocess_exec(
                'git', 'log', '--oneline', '--max-count=5', f'HEAD..origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            diff_text, _ = await proc_diff.communicate()
            
            summary = diff_text.decode().strip() or "No commit summary available."
            update_prompt = (
                f"🚀 **New Updates Found!**\n\n"
                f"📂 **Branch:** `{branch}`\n"
                f"✨ **Latest Changes:**\n```\n{summary}```\n\n"
                f"⚠️ *Run `.update -f` to apply these changes and restart.*"
            )
            return await status_msg.edit(update_prompt)

        # 4. Execution Phase (Forced)
        def get_file_hash(filepath):
            if not os.path.exists(filepath): return ""
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()

        req_hash_before = get_file_hash("requirements.txt")

        await status_msg.edit(f"🔄 *Applying updates from `{branch}`...*")
        proc_reset = await asyncio.create_subprocess_exec(
            'git', 'reset', '--hard', f'origin/{branch}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc_reset.communicate()
        
        if proc_reset.returncode != 0:
            return await status_msg.edit(f"❌ *Reset failed:* {stderr.decode()}")

        # 5. Dependency Sync
        req_hash_after = get_file_hash("requirements.txt")
        
        if req_hash_after != req_hash_before:
            await status_msg.edit("📦 *Requirements changed. Installing dependencies...*")
            pip_proc = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await pip_proc.communicate()
            
            if pip_proc.returncode != 0:
                 await status_msg.edit("⚠️ *Warning:* Dependency installation failed. Bot might crash after restart.")

        # 6. Finalization
        await status_msg.edit("✅ **Update Complete!**\n\n*Restarting Astra Userbot to apply changes...*")
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as e:
        await status_msg.edit(f"❌ *System Error during update:* {str(e)}")

@astra_command(
    name="reload",
    description="Hot-reloads all plugins and project modules.",
    category="System",
    owner_only=True
)
async def reload_cmd(client: Client, message: Message):
    """Hot-reloads all plugins and project modules."""
    status_msg = await smart_reply(message, "⏳ *Hot-reloading Astra Userbot...*")
    
    try:
        from utils.plugin_utils import reload_all_plugins
        count = reload_all_plugins(client)
        
        await asyncio.sleep(0.5)
        await status_msg.edit(
            f"✅ **Reload Successful!**\n"
            f"📦 **Modules:** {count} plugins resynced.\n"
            f"🕒 **Time:** {time.strftime('%H:%M:%S')}"
        )
    except Exception as e:
        await report_error(client, e, context='Reload command failure')

@astra_command(
    name="logs",
    description="Fetch the recent bot logs or the full log file.",
    category="System",
    owner_only=True,
    usage=".logs [full]"
)
async def logs_cmd(client: Client, message: Message):
    """
    Fetches the last 50 lines of logs as text.
    Uploads the full log file if 'full' is passed as an argument.
    """
    args = extract_args(message)
    is_full = "full" in [a.lower() for a in args]
    
    status_msg = await smart_reply(message, "⏳ *Retrieving logs...*")
    
    log_file = "astra_full_debug.txt"
    if not os.path.exists(log_file):
        return await status_msg.edit("❌ *Error:* Log file `astra_full_debug.txt` not found.")

    try:
        # Read the last 50 lines for a quick preview
        with open(log_file, "r") as f:
            lines = f.readlines()
            recent_logs = "".join(lines[-50:])
        
        # Format for WhatsApp
        preview = f"📜 **Recent Logs (Last 50 Lines):**\n```\n{recent_logs}\n```"
        
        # Always send text preview (unless logs are empty)
        if recent_logs:
            await status_msg.edit(preview)
        else:
            await status_msg.edit("ℹ️ *Log file is currently empty.*")
        
        # Upload full file ONLY if requested
        if is_full:
            await smart_reply(message, "📤 *Uploading full log file...*")
            import base64
            with open(log_file, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')
                
            media = {
                "mimetype": "text/plain",
                "data": b64_data,
                "filename": "astra_logs.txt"
            }
            
            await client.send_media(
                message.chat_id,
                media,
                caption="📄 **Full Astra Debug Logs**",
                reply_to=message.id
            )

    except Exception as e:
        await status_msg.edit(f"❌ *Error retrieving logs:* {str(e)}")
