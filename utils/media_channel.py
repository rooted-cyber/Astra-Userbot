# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import os
import time
import json
import re
import asyncio
from typing import Optional, Callable
from astra.client import Client
from astra.models import Message
from config import config
from utils.helpers import safe_edit
from utils.progress import get_progress_bar

class MediaChannel:
    """
    Centralized Media Downloader and Uploader Channel.
    Provides real-time progress tracking and optimized delivery.
    """
    
    def __init__(self, client: Client, message: Message, status_msg: Message):
        self.client = client
        self.message = message
        self.status_msg = status_msg
        self.last_update = 0
        self.update_interval = 0.5  # Dynamic high-speed updates (0.5s)

    async def _update_status(self, text: str, force: bool = False, is_progress: bool = False):
        """Throttled status updates for smooth UI."""
        from utils.state import state
        # Silent mode (FAST_MEDIA) bypasses progress updates
        if is_progress and state.get_config("FAST_MEDIA"):
            return

        now = time.time()
        if force or (now - self.last_update >= self.update_interval):
            await safe_edit(self.status_msg, text)
            self.last_update = now

    async def run_bridge(self, url: str, mode: str):
        """Executes the JS downloader bridge and handles output streams."""
        bridge_script = os.path.join(os.path.dirname(__file__), "js_downloader.js")
        cookies_file = getattr(config, 'YOUTUBE_COOKIES_FILE', '') or ''
        cookies_browser = getattr(config, 'YOUTUBE_COOKIES_FROM_BROWSER', '') or ''

        process = await asyncio.create_subprocess_exec(
            "node", bridge_script,
            url, mode, 
            cookies_file, cookies_browser,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        metadata = {"title": "Media Content", "platform": "Astra", "uploader": "Unknown", "url": url}
        file_path = None

        while True:
            line = await process.stdout.readline()
            if not line: break
            
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            # Metadata Capture
            if line_str.startswith("METADATA:"):
                metadata.update(json.loads(line_str.replace("METADATA:", "")))
                await self._update_status(
                    f"✨ *{metadata['title']}*\n"
                    f"🌐 *Platform:* {metadata['platform']}\n"
                    f"📂 *Mode:* {mode.capitalize()}\n\n"
                    f"⏳ *Preparing download...*",
                    force=True
                )

            # Progress Capture
            if "[download]" in line_str and "%" in line_str:
                match = re.search(r"(\d+\.\d+)% of\s+([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+(\d+:\d+)", line_str)
                if match:
                    pct, size, speed, eta = match.groups()
                    bar = get_progress_bar(float(pct))
                    await self._update_status(
                        f"✨ *{metadata['title']}*\n"
                        f"🌐 *Platform:* {metadata['platform']}\n\n"
                        f"📥 *Downloading:* {bar}\n"
                        f"📋 *Size:* `{size}`\n"
                        f"⚡ *Speed:* `{speed}`\n"
                        f"⏳ *Remaining:* `{eta}`",
                        is_progress=True
                    )

            # Success Capture
            if line_str.startswith("SUCCESS:"):
                res = json.loads(line_str.replace("SUCCESS:", ""))
                files = res.get('files', [])
                if files: file_path = files[0]

        await process.wait()
        if process.returncode != 0:
            stderr = (await process.stderr.read()).decode(errors='ignore')[:300]
            raise Exception(f"Bridge Error: {stderr}")

        if not file_path or not os.path.exists(file_path):
            raise Exception("File not found after download.")

        return file_path, metadata

    async def upload_file(self, file_path: str, metadata: dict, mode: str):
        """Uploads file with real-time progress bar."""
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        size_str = f"{file_size_mb:.2f} MB" if file_size_mb < 1024 else f"{file_size_mb/1024:.2f} GB"
        
        start_time = time.time()

        async def on_progress(current, total):
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            
            elapsed = time.time() - start_time
            if elapsed > 0:
                sent_mb = (current / total) * file_size_mb
                speed = sent_mb / elapsed
                speed_text = f"{speed:.2f} MiB/s"
            else:
                speed_text = "..."

            await self._update_status(
                f"✨ *{metadata['title']}*\n"
                f"🌐 *Platform:* {metadata['platform']}\n\n"
                f"📤 *Uploading:* {bar}\n"
                f"⚡ *Speed:* `{speed_text}`",
                is_progress=True
            )

        caption = (
            f"✨ *{metadata['title']}*\n"
            f"👤 *Author:* {metadata.get('uploader', 'Unknown')}\n"
            f"📁 *Size:* `{size_str}`\n"
            f"🔗 *Source:* {metadata.get('url', 'Unknown')}\n\n"
            f"🚀 *Powered by Astra UserBot*"
        )

        try:
            if mode == "audio":
                await self.client.send_audio(self.message.chat_id, file_path, reply_to=self.message.id, progress=on_progress)
            else:
                await self.client.send_video(self.message.chat_id, file_path, caption=caption, reply_to=self.message.id, progress=on_progress)
            
            await self.status_msg.delete()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
