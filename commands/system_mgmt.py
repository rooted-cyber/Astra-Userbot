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
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

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
    await edit_or_reply(
        message, 
        f"{UI.header('SYSTEM REBOOT')}\n"
        f"Status : {UI.mono('[ BUSY ]')} Initializing restart sequence...\n"
        f"Uptime : {UI.mono(uptime)}\n\n"
        f"{UI.italic('Astra process will be re-spawned momentarily.')}"
    )
    
    time.sleep(1.5)
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
    await edit_or_reply(
        message, 
        f"{UI.header('SYSTEM SHUTDOWN')}\n"
        f"Status : {UI.mono('[ BUSY ]')} Terminating core engines...\n"
        f"Uptime : {UI.mono(uptime)}\n\n"
        f"{UI.mono('[ WARN ]')} Manual restart required via console/host."
    )
    
    time.sleep(1.5)
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
    status_msg = await edit_or_reply(message, f"{UI.header('DIAGNOSTICS')}\n{UI.mono('[ BUSY ]')} Scanning system vitals...")
    
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
            f"{UI.header('SYSTEM HEALTH')}\n"
            f"Uptime   : {UI.mono(uptime)}\n"
            f"Memory   : {UI.mono(get_size_format(proc_mem))} (Process)\n"
            f"CPU Load : {UI.mono(f'{cpu_usage}%')}\n"
            f"System V : {UI.mono(f'{memory.percent}%')} RAM\n"
            f"Disk Avl : {UI.mono(get_size_format(disk.free))}\n\n"
            f"{UI.bold('DATABASE REGISTRY')}\n"
            f"• Records: {UI.mono(db_stats['sqlite']['state_records'])} state | {UI.mono(db_stats['sqlite']['meme_records'])} cache\n"
            f"• Storage: {UI.mono(f'{db_stats['sqlite']['size_mb']} MB')} (SQLite)\n"
            f"• MongoDB: {UI.mono('[ CONNECTED ]') if db_stats['mongodb']['connected'] else UI.mono('[ FAIL ]')}\n\n"
            f"{UI.italic('All systems operating within nominal parameters.')}"
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
            f"{UI.header('PLATFORM MANIFEST')}\n"
            f"OS Type  : {UI.mono(os_info)}\n"
            f"Arch     : {UI.mono(arch_info)}\n"
            f"Python   : {UI.mono(python_ver)}\n"
            f"Platform : {UI.mono(platform.platform())}\n"
            f"Boot UTC : {UI.mono(datetime.fromtimestamp(BOOT_TIME).strftime('%Y-%m-%d %H:%M:%S'))}\n"
        )
        await edit_or_reply(message, report)
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="SysInfo Failure")

# Files to protect during force update (never overwritten by git reset)
PROTECTED_FILES = [".env", "config.env", "session.data", "astra.db"]

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
    
    status_msg = await edit_or_reply(message, f"{UI.header('UPDATE ENGINE')}\n{UI.mono('[ BUSY ]')} Synchronizing with {UI.mono(branch)}...")
    
    try:
        if not os.path.exists(".git"):
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Repository manifest not found (.git missing).")

        # Fetch latest from remote
        await status_msg.edit(f"{UI.header('UPDATE ENGINE')}\n{UI.mono('[ BUSY ]')} Fetching remote assets: {UI.mono(branch)}...")
        proc = await asyncio.create_subprocess_exec(
            'git', 'fetch', 'origin', branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Fetch failure:\n{UI.mono(stderr.decode().strip())}")

        # Compare local vs remote
        proc_local = await asyncio.create_subprocess_exec('git', 'rev-parse', 'HEAD', stdout=asyncio.subprocess.PIPE)
        local_hash_raw, _ = await proc_local.communicate()
        proc_remote = await asyncio.create_subprocess_exec('git', 'rev-parse', f'origin/{branch}', stdout=asyncio.subprocess.PIPE)
        remote_hash_raw, _ = await proc_remote.communicate()
        
        local_hash = local_hash_raw.decode().strip()
        remote_hash = remote_hash_raw.decode().strip()

        # Get changelog (commits between local and remote)
        changelog = ""
        commit_count = 0
        if local_hash != remote_hash:
            proc_diff = await asyncio.create_subprocess_exec(
                'git', 'log', '--format=%h | %s', '--max-count=10', f'HEAD..origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            diff_text, _ = await proc_diff.communicate()
            changelog = diff_text.decode().strip() or "Minor internal improvements."
            
            # Count total commits
            proc_count = await asyncio.create_subprocess_exec(
                'git', 'rev-list', '--count', f'HEAD..origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            count_text, _ = await proc_count.communicate()
            try:
                commit_count = int(count_text.decode().strip())
            except:
                commit_count = len(changelog.split('\n'))

        # Already up to date
        if local_hash == remote_hash and not force:
            return await status_msg.edit(
                f"{UI.header('SYSTEM UPDATE')}\n"
                f"Branch  : {UI.mono(branch)}\n"
                f"Build   : {UI.mono(local_hash[:7])}\n"
                f"Version : {UI.mono(config.VERSION)}\n\n"
                f"{UI.mono('[ OK ]')} System is currently synchronized."
            )

        # Show changelog and prompt for force update
        if not force:
            # Check for uncommitted changes
            proc_status = await asyncio.create_subprocess_exec(
                'git', 'status', '--porcelain',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_status, _ = await proc_status.communicate()
            has_local_changes = bool(stdout_status.strip())

            proc_author = await asyncio.create_subprocess_exec(
                'git', 'log', '-1', '--format=%an', f'origin/{branch}',
                stdout=asyncio.subprocess.PIPE
            )
            author_text, _ = await proc_author.communicate()
            author_name = author_text.decode().strip() or "Astra Dev"
            
            update_prompt = (
                f"{UI.header('UPDATE AVAILABLE')}\n"
                f"Scope   : {UI.mono(f'{commit_count} commit(s)')}\n"
                f"Branch  : {UI.mono(branch)}\n"
                f"Author  : {UI.mono(author_name)}\n"
                f"Diff    : {UI.mono(local_hash[:7])} -> {UI.mono(remote_hash[:7])}\n\n"
                f"{UI.bold('CHANGELOG:')}\n```\n{changelog}```\n"
            )
            if has_local_changes:
                update_prompt += f"\n{UI.mono('[ WARN ]')} Local modifications detected (will be overwritten).\n"
            update_prompt += (
                f"\n{UI.italic('Protected scope: .env, config.env, session.data, astra.db')}\n"
                f"Action  : {UI.mono('.update -f')} to apply and reboot."
            )
            return await status_msg.edit(update_prompt)

        # ── Force Update ──
        # 1. Backup protected files
        backups = {}
        for pf in PROTECTED_FILES:
            if os.path.exists(pf):
                with open(pf, "rb") as f:
                    backups[pf] = f.read()

        def get_file_hash(filepath):
            if not os.path.exists(filepath): return ""
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()

        req_hash_before = get_file_hash("requirements.txt")
        await status_msg.edit(
            f"{UI.header('UPDATE ENGINE')}\n"
            f"{UI.mono('[ BUSY ]')} Applying {commit_count} synchronization nodes ({UI.mono(branch)})...\n"
            f"{UI.mono('[ OK ]')} Protected assets secured."
        )
        
        # 2. Hard reset to remote
        proc_reset = await asyncio.create_subprocess_exec(
            'git', 'reset', '--hard', f'origin/{branch}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc_reset.communicate()
        
        if proc_reset.returncode != 0:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Synchronization failed:\n{UI.mono(stderr.decode().strip())}")

        # 3. Restore protected files
        for pf, data in backups.items():
            try:
                with open(pf, "wb") as f:
                    f.write(data)
            except Exception:
                pass

        # 4. Install new deps if requirements.txt changed
        req_hash_after = get_file_hash("requirements.txt")
        if req_hash_after != req_hash_before:
            await status_msg.edit(f"{UI.header('DEP MANAGER')}\n{UI.mono('[ BUSY ]')} Installing revised dependency nodes...")
            pip_proc = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await pip_proc.communicate()

        # 5. Show final report and restart
        final_report = (
            f"{UI.header('UPDATE COMPLETE')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📂 **Branch:** `{branch}`\n"
            f"🏷️ **Build:** `{remote_hash[:7]}`\n"
            f"� **Changes:** {commit_count} commit{'s' if commit_count != 1 else ''}\n"
        )
        if changelog:
            short_log = '\n'.join(changelog.split('\n')[:5])
            final_report += f"\n```\n{short_log}```\n"
        if backups:
            final_report += f"\n🔐 **Restored:** `{', '.join(backups.keys())}`\n"
        final_report += "\n�🚀 _Astra is restarting to apply changes..._"
        
        await status_msg.edit(final_report)
        time.sleep(1.5)
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
    status_msg = await edit_or_reply(message, f"{UI.header('CORE RELOAD')}\n{UI.mono('[ BUSY ]')} Resyncing all plugin nodes...")
    
    try:
        from utils.plugin_utils import reload_all_plugins
        count = reload_all_plugins(client)
        
        await status_msg.edit(
            f"{UI.header('RELOAD SUCCESS')}\n"
            f"Nodes   : {UI.mono(f'{count} synchronized')}\n"
            f"Stamp   : {UI.mono(time.strftime('%H:%M:%S'))}\n\n"
            f"{UI.italic('System core is now fresh.')}"
        )
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Module Reload Failure")

@astra_command(
    name="logs",
    description="Retrieves recent Astra system logs with noise reduction.",
    category="System",
    owner_only=True,
    usage=".logs [full]",
)
async def logs_cmd(client: Client, message: Message):
    """Fetches diagnostic logs, filtering repetitive startup noise."""
    args = extract_args(message)
    is_full = "full" in [a.lower() for a in args]

    log_file = "astra_full_debug.txt"
    if not os.path.exists(log_file):
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Diagnostic log manifest not found.")

    status_msg = await edit_or_reply(message, f"{UI.header('TERMINAL CONSOLE')}\n{UI.mono('[ BUSY ]')} Fetching system logs...")

    # ── Noise Reduction Engine ──
    # Patterns that indicate startup noise (collapsed into single markers)
    NOISE_PATTERNS = [
        "ASTRA BOT STARTUP",
        "=" * 20,
        "Applied stability patch",
        "Applied framework patch",
        "randomized delays",
        "Message.edit now uses",
    ]

    def is_noise(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return True
        for pattern in NOISE_PATTERNS:
            if pattern in stripped:
                return True
        return False

    def extract_timestamp(line: str) -> str:
        """Try to extract timestamp from a log line."""
        parts = line.split(" - ", 1)
        if parts:
            ts = parts[0].strip()
            if len(ts) > 10:
                return ts
        return ""

    def get_filtered_logs(filename, n=200):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = list(f)

        filtered = []
        in_noise_block = False
        last_startup_ts = None

        for line in all_lines:
            if is_noise(line):
                # Track timestamp from startup lines
                ts = extract_timestamp(line)
                if ts:
                    last_startup_ts = ts
                in_noise_block = True
                continue

            # When exiting a noise block, insert a single marker
            if in_noise_block:
                in_noise_block = False
                if last_startup_ts:
                    filtered.append(f"── {UI.mono(f'[ REBOOT @ {last_startup_ts} ]')} ──\n")
                last_startup_ts = None

            filtered.append(line)

        return filtered[-n:]

    lines = get_filtered_logs(log_file)
    log_content = "".join(lines).strip()

    if not log_content:
        return await status_msg.edit(f"{UI.mono('[ EMPTY ]')} System console buffer is null.")

    # Truncation for WhatsApp message limits
    if len(log_content) > 3500:
        log_content = "...\n" + log_content[-3500:]

    from datetime import datetime
    from zoneinfo import ZoneInfo
    now_india = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%H:%M:%S")

    output = (
        f"{UI.header('SYSTEM CONSOLE')}\n"
        f"```\n{log_content}\n```\n"
        f"Fetched at : {UI.mono(now_india)}\n"
        f"Scope : {UI.mono(f'{len(lines)} lines (noise filtered)')}"
    )

    await status_msg.edit(output)

    if is_full:
        status2 = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Uploading comprehensive log manifest...")
        import base64
        with open(log_file, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        media = {"mimetype": "text/plain", "data": b64_data, "filename": "astra_full_logs.txt"}
        await client.send_photo(message.chat_id, media, caption=f"{UI.mono('[ OK ]')} Full System Manifest", reply_to=message.id)
        await status2.delete()


@astra_command(
    name="clearcache",
    description="Clears the media gateway cache.",
    category="System",
    aliases=["ccache"],
    owner_only=True
)
async def clearcache_cmd(client: Client, message: Message):
    """Purges the media cache directory."""
    status_msg = await edit_or_reply(message, f"{UI.header('MAINTENANCE')}\n{UI.mono('[ BUSY ]')} Purging media cache...")
    try:
        from utils.cache_manager import cache
        result = cache.clear_cache()
        if result["success"]:
            await status_msg.edit(
                f"{UI.header('CACHE PURGED')}\n"
                f"Deleted   : {UI.mono(f'{result['files_deleted']} files')}\n"
                f"Recovered : {UI.mono(f'{result['freed_mb']} MB')}\n\n"
                f"{UI.italic('Disk space optimized.')}"
            )
        else:
            await status_msg.edit(f"{UI.mono('[ ERROR ]')} Purge failed: {UI.mono(result.get('error'))}")
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
        msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Scanning Astra core...")
        time.sleep(0.5)
        await msg.edit(f"{UI.header('ASTRA PRO ONLINE')}\n{UI.italic('System core is responsive and ready for your commands.')}")
    except Exception as e:
        from utils.error_reporter import ErrorReporter
        await ErrorReporter.report(client, message, e, context="Start Check Failure")
