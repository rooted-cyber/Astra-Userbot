import os
import sys
import asyncio
import time
import hashlib
import platform
import shutil
import psutil
import traceback
from datetime import datetime
from config import config
from . import *

# Utility for uptime calculation
from utils.state import BOOT_TIME
from utils.database import db

def get_uptime_str():
    """Returns a professional uptime string."""
    delta = int(time.time() - BOOT_TIME)
    days = delta // 86400
    hours = (delta % 86400) // 3600
    minutes = (delta % 3600) // 60
    
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "just now"

def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"

@astra_command(
    name="restart",
    description="Restarts the Astra Userbot process.",
    category="System",
    owner_only=True
)
async def restart_cmd(client: Client, message: Message):
    """Restart Bot"""
    uptime = get_uptime_str()
    await smart_reply(
        message, 
        f"🔄 **Astra System Reboot**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛰️ **Status:** Initializing restart sequence...\n"
        f"🕒 **Uptime:** `{uptime}`\n\n"
        f"💡 _Astra will be back online in seconds._"
    )
    
    await asyncio.sleep(1.5)
    os.execv(sys.executable, [sys.executable] + sys.argv)

@astra_command(
    name="shutdown",
    description="Shuts down the Astra Userbot process.",
    category="System",
    owner_only=True
)
async def shutdown_cmd(client: Client, message: Message):
    """Shutdown Bot"""
    uptime = get_uptime_str()
    await smart_reply(
        message, 
        f"⏻ **Astra Power Off**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛑 **Status:** Shutting down core engines...\n"
        f"🕒 **Uptime:** `{uptime}`\n\n"
        f"⚠️ _Manual intervention required to start again._"
    )
    
    await asyncio.sleep(1.5)
    sys.exit(0)

@astra_command(
    name="health",
    description="Displays comprehensive system health and database diagnostics.",
    category="System",
    owner_only=True,
    aliases=["status", "h"]
)
async def health_cmd(client: Client, message: Message):
    """System Health Diagnostics"""
    status_msg = await smart_reply(message, "🏥 **Astra Diagnostics**\n━━━━━━━━━━━━━━━━━━━━\n🧬 *Scanning system vitals...*")
    
    try:
        # 1. System Metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 2. Database Metrics
        db_stats = await db.get_stats()
        
        # 3. Process Info
        proc = psutil.Process(os.getpid())
        proc_mem = proc.memory_info().rss
        
        uptime = get_uptime_str()
        
        health_report = (
            f"🏥 **Astra System Health**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛰️ **Uptime:** `{uptime}`\n"
            f"🧠 **Memory:** `{get_size_format(proc_mem)}` (used by bot)\n"
            f"📊 **System CPU:** `{cpu_usage}%`\n"
            f"💾 **System RAM:** `{memory.percent}%` used\n"
            f"📂 **Disk Space:** `{get_size_format(disk.free)}` free\n\n"
            f"🗄️ **Database Stats**\n"
            f"• Records: `{db_stats['sqlite']['state_records']}` state | `{db_stats['sqlite']['meme_records']}` memes\n"
            f"• Disk Usage: `{db_stats['sqlite']['size_mb']} MB` (SQLite)\n"
            f"• MongoDB: `{'✅ Connected' if db_stats['mongodb']['connected'] else '❌ Disconnected'}`\n\n"
            f"✨ _System is operating within optimal parameters._"
        )
        
        await status_msg.edit(health_report)
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Health Check Failure")

@astra_command(
    name="sysinfo",
    description="Displays detailed information about the hosting environment.",
    category="System",
    owner_only=True,
    aliases=["sys", "platform"]
)
async def sysinfo_cmd(client: Client, message: Message):
    """Detailed System Info"""
    try:
        os_info = f"{platform.system()} {platform.release()}"
        arch_info = platform.machine()
        python_ver = platform.python_version()
        
        report = (
            f"🖥️ **System Information**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 **OS:** `{os_info}`\n"
            f"🧠 **Arch:** `{arch_info}`\n"
            f"🐍 **Python:** `{python_ver}`\n"
            f"⚙️ **Platform:** `{platform.platform()}`\n"
            f"📅 **Booted:** `{datetime.fromtimestamp(BOOT_TIME).strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await smart_reply(message, report)
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="SysInfo Failure")

@astra_command(
    name="update",
    description="Updates Astra from the GitHub repository.",
    category="System",
    owner_only=True,
    usage=".update [-b branch] [-f]"
)
async def update_cmd(client: Client, message: Message):
    """ Advanced Update Handler """
    args = extract_args(message)
    force = "-f" in args
    branch = "master"
    if "-b" in args:
        idx = args.index("-b")
        if len(args) > idx + 1:
            branch = args[idx + 1]
    
    status_msg = await smart_reply(message, f"📡 **Astra Update Engine**\n━━━━━━━━━━━━━━━━━━━━\n🔍 *Syncing with `{branch}`...*")
    
    try:
        if not os.path.exists(".git"):
            return await status_msg.edit("❌ **Error:** Directory is not a git repository.")

        if not force:
            proc_status = await asyncio.create_subprocess_exec(
                'git', 'status', '--porcelain',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_status, _ = await proc_status.communicate()
            if stdout_status.strip():
                return await status_msg.edit(
                    f"⚠️ **Uncommitted Changes Detected**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"You have local modifications that would be overwritten by a reset.\n\n"
                    f"💡 *Options:*\n"
                    f"1. Commit your changes locally.\n"
                    f"2. Use `.update -f` to overwrite them (irreversible)."
                )

        await status_msg.edit(f"📥 **Astra Update Engine**\n━━━━━━━━━━━━━━━━━━━━\n📡 *Fetching updates for:* `{branch}`...")
        proc = await asyncio.create_subprocess_exec(
            'git', 'fetch', 'origin', branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return await status_msg.edit(f"❌ **Fetch Failed**\n━━━━━━━━━━━━━━━━━━━━\n`{stderr.decode().strip()}`")

        proc_local = await asyncio.create_subprocess_exec('git', 'rev-parse', 'HEAD', stdout=asyncio.subprocess.PIPE)
        local_hash_raw, _ = await proc_local.communicate()
        
        proc_remote = await asyncio.create_subprocess_exec('git', 'rev-parse', f'origin/{branch}', stdout=asyncio.subprocess.PIPE)
        remote_hash_raw, _ = await proc_remote.communicate()
        
        local_hash = local_hash_raw.decode().strip()
        remote_hash = remote_hash_raw.decode().strip()

        if local_hash == remote_hash and not force:
            return await status_msg.edit(
                f"✅ **Astra is up to date**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📂 **Branch:** `{branch}`\n"
                f"🏷️ **Build:** `{local_hash[:7]}`\n"
                f"🚀 **Version:** `{config.VERSION}`\n\n"
                f"✨ _No new updates found._"
            )

        if local_hash != remote_hash and not force:
            proc_diff = await asyncio.create_subprocess_exec(
                'git', 'log', '--format=%h | %s', '--max-count=5', f'HEAD..origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            diff_text, _ = await proc_diff.communicate()
            
            proc_author = await asyncio.create_subprocess_exec(
                'git', 'log', '-1', '--format=%an', f'origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            author_text, _ = await proc_author.communicate()
            author_name = author_text.decode().strip() or "Astra Dev"
            summary = diff_text.decode().strip() or "Minor internal improvements."
            
            update_prompt = (
                f"🚀 **Update Available**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📂 **Branch:** `{branch}`\n"
                f"👤 **Author:** `{author_name}`\n\n"
                f"📋 **Changelog:**\n```\n{summary}```\n\n"
                f"⚠️ *Type `.update -f` to apply changes and restart.*"
            )
            return await status_msg.edit(update_prompt)

        def get_file_hash(filepath):
            if not os.path.exists(filepath): return ""
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()

        req_hash_before = get_file_hash("requirements.txt")
        await status_msg.edit(f"🔄 **Astra Update Engine**\n━━━━━━━━━━━━━━━━━━━━\n⚙️ *Merging updates from `{branch}`...*")
        
        proc_reset = await asyncio.create_subprocess_exec(
            'git', 'reset', '--hard', f'origin/{branch}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc_reset.communicate()
        
        if proc_reset.returncode != 0:
            return await status_msg.edit(f"❌ **Update Failed**\n━━━━━━━━━━━━━━━━━━━━\n`{stderr.decode().strip()}`")

        req_hash_after = get_file_hash("requirements.txt")
        if req_hash_after != req_hash_before:
            await status_msg.edit(f"📦 **Astra Update Engine**\n━━━━━━━━━━━━━━━━━━━━\n📦 *Installing new dependencies...*")
            pip_proc = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await pip_proc.communicate()

        await status_msg.edit("✅ **Update Complete**\n━━━━━━━━━━━━━━━━━━━━\n🚀 _Astra is restarting to apply changes..._")
        await asyncio.sleep(1.5)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="System Update Failure")

@astra_command(
    name="reload",
    description="Hot-reloads all Astra modules and plugins.",
    category="System",
    owner_only=True
)
async def reload_cmd(client: Client, message: Message):
    """Hot-reloads all plugins and project modules."""
    status_msg = await smart_reply(message, "⏳ **Astra Hot-Reload**\n━━━━━━━━━━━━━━━━━━━━\n🔄 *Resyncing all modules...*")
    
    try:
        from utils.plugin_utils import reload_all_plugins
        count = reload_all_plugins(client)
        
        await status_msg.edit(
            f"✅ **Reload Successful**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 **Plugins:** `{count}` resynced\n"
            f"🕒 **Time:** `{time.strftime('%H:%M:%S')}`\n\n"
            f"✨ _System core is now fresh._"
        )
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Module Reload Failure")

@astra_command(
    name="logs",
    description="Retrieves recent Astra system logs.",
    category="System",
    owner_only=True,
    usage=".logs [full]"
)
async def logs_cmd(client: Client, message: Message):
    """Fetches last 100 lines or uploads full file."""
    args = extract_args(message)
    is_full = "full" in [a.lower() for a in args]
    
    log_file = "astra_full_debug.txt"
    if not os.path.exists(log_file):
        return await smart_reply(message, "❌ **Error:** Log file not found.")

    status_msg = await smart_reply(message, "⏳ **Log Retrieval**\n━━━━━━━━━━━━━━━━━━━━\n📝 *Reading Astra console...*")
    
    try:
        def tail(filename, n=100):
            from collections import deque
            with open(filename, "r", encoding='utf-8', errors='ignore') as f:
                return list(deque(f, n))

        lines = tail(log_file)
        log_content = "".join(lines)
        if not log_content: return await status_msg.edit("ℹ️ **Console is empty.**")

        if len(log_content) > 3500: log_content = log_content[-3500:]
            
        await status_msg.edit(f"📜 **Astra Live Console**\n━━━━━━━━━━━━━━━━━━━━\n```\n{log_content}\n```\n🕒 **Last Check:** `{time.strftime('%H:%M:%S')}`")
        
        if is_full:
            await smart_reply(message, "📤 *Uploading full log file...*")
            import base64
            with open(log_file, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')
                
            media = {"mimetype": "text/plain", "data": b64_data, "filename": "astra_full_logs.txt"}
            await client.send_media(message.chat_id, media, caption="📄 **Full Astra System Logs**", reply_to=message.id)
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Log Retrieval Failure")

@astra_command(
    name="clearcache",
    description="Clears the media gateway cache.",
    category="System",
    aliases=["ccache"],
    owner_only=True
)
async def clearcache_cmd(client: Client, message: Message):
    """Purges the media cache directory."""
    status_msg = await smart_reply(message, "🧹 **Maintenance**\n━━━━━━━━━━━━━━━━━━━━\n🗑️ *Clearing media cache...*")
    try:
        from utils.cache_manager import cache
        result = cache.clear_cache()
        if result["success"]:
            await status_msg.edit(f"✅ **Cache Purged**\n━━━━━━━━━━━━━━━━━━━━\n🗑️ **Deleted:** `{result['files_deleted']}` files\n💾 **Recovered:** `{result['freed_mb']} MB`\n\n🚀 _Disk space optimized._")
        else:
            await status_msg.edit(f"❌ **Purge Failed**\n━━━━━━━━━━━━━━━━━━━━\n`{result.get('error')}`")
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Cache Purge Failure")

@astra_command(
    name="start",
    description="Bot health check and responsiveness test.",
    category="System",
    owner_only=True,
    aliases=["test"]
)
async def start_cmd(client: Client, message: Message):
    """Test command to verify bot responsiveness."""
    try:
        msg = await smart_reply(message, "🤖 **Scanning Astra core...**")
        await asyncio.sleep(0.5)
        await msg.edit("🤖 **Astra Userbot is active!**\n\n🚀 _System core is responsive and ready for your commands._")
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Start Check Failure")
