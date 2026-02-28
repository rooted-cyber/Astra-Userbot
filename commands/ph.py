# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import asyncio
import re
import platform
import socket
import requests
from . import *

def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

@astra_command(
    name="ph",
    description="Display phone/system information using an external script and local fallback.",
    category="Tools & Utilities",
    aliases=["phoneinfo"],
    owner_only=True
)
async def phone_cmd(client, message):
    msg = await message.reply("📲 *Fetching phone/system information...*")

    try:
        # 1. Run the external script (from user request)
        process = await asyncio.create_subprocess_shell(
            'curl -fsSL https://gist.githubusercontent.com/rooted-cyber/cdb6533f500f53dd46404968794bec9a/raw/phone.sh -o phone.sh && bash phone.sh',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        raw_output = stdout.decode() + stderr.decode()
        
        # 2. Cleanup output
        clean_output = strip_ansi_codes(raw_output).strip()
        
        # 3. Handle Termux-only limitation or script failure
        if "Only for termux" in clean_output or not clean_output:
            # Fallback to local Python-based hardware/OS info if script fails or is restricted
            os_info = f"{platform.system()} {platform.release()}"
            arch = platform.machine()
            py_ver = platform.python_version()
            hostname = socket.gethostname()
            
            # Fetch IP info
            try:
                ip_info = requests.get("https://ifconfig.me/all.json", timeout=5).json()
                ip = ip_info.get("ip_addr", "Unknown")
                country = ip_info.get("country_code", "Unknown")
            except:
                ip = "Unknown"
                country = "Unknown"

            fallback_msg = (
                "💻 **SYSTEM INFORMATION FALLBACK** 💻\n"
                "*(Script failed or requires Termux)*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏠 **OS:** `{os_info}`\n"
                f"🧠 **Arch:** `{arch}`\n"
                f"🏷️ **Hostname:** `{hostname}`\n"
                f"🌐 **IP:** `{ip}` ({country})\n"
                f"🐍 **Python:** `{py_ver}`\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ *System diagnostics complete.*"
            )
            await msg.edit(fallback_msg)
            return

        # 4. Success-ish: Truncate and display script output (without ANSI trash)
        if len(clean_output) > 4000:
            clean_output = clean_output[:4000] + "\n\n...Output Truncated..."

        await msg.edit(f"✅ **Phone Info (Script Results):**\n\n```{clean_output}```")

    except Exception as e:
        await msg.edit(f"❌ **Error executing command:**\n`{str(e)}`")
    finally:
        # Cleanup temporary script file
        if os.path.exists("phone.sh"):
            try: os.remove("phone.sh")
            except: pass
