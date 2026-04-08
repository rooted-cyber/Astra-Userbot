"""
Astra Userbot — Main Entry Point
"""

import asyncio
import logging
import os
import random
import signal
import sys
import threading
import time
from typing import *

import requests
from flask import Flask

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

from utils.logger import Colors, setup_logging
from astra import Client, Message

setup_logging(SCRIPT_DIR)
logger = logging.getLogger("AstraBot")


# --- Stability Patches ---
def apply_framework_patches():
    original_edit = Message.edit

    async def patched_edit(self, text: str, **kwargs) -> bool:
        import asyncio
        await asyncio.sleep(0.5)
        try:
            return await original_edit(self, text, **kwargs)
        except Exception:
            # Suppress errors for failed edits as requested
            return False

    Message.edit = patched_edit

apply_framework_patches()

from config import config


def print_banner():
    import socket
    ip = "127.0.0.1"
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        pass

    print(f"\n {Colors.BOLD}{Colors.CYAN}ASTRA USERBOT{Colors.END}")
    print(f" {Colors.GRAY}──────────────{Colors.END}")
    print(f" {Colors.CYAN}ver{Colors.END} {config.VERSION}")
    print(f" {Colors.CYAN}ip{Colors.END} {ip}")
    print(f" {Colors.CYAN}pid{Colors.END} {os.getpid()}")
    print(f" {Colors.GRAY}──────────────{Colors.END}\n")


def patch_authenticator(client_instance):
    auth = client_instance.authenticator
    original_qr = auth._display_qr
    original_code = auth._display_code

    def patched_qr(data):
        with open(os.path.join(SCRIPT_DIR, "qr_data.txt"), "w") as f:
            f.write(data)
        original_qr(data)

    def patched_code(code):
        with open(os.path.join(SCRIPT_DIR, "pairing_code.txt"), "w") as f:
            f.write(code)
        original_code(code)

    auth._display_qr = patched_qr
    auth._display_code = patched_code


# --- Client ---
client = Client(
    session_id=os.getenv("ASTRA_SESSION_ID", "X"),
    phone=os.getenv("PHONE_NUMBER") or os.getenv("BOT_OWNER_ID"),
    headless=os.getenv("ASTRA_HEADLESS", "True").lower() == "true",
)
patch_authenticator(client)


# --- Flask Health Check ---
app = Flask(__name__)

@app.route("/")
def home():
    return {"status": "Astra live", "version": config.VERSION}

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    url = os.environ.get("PING_URL", "").strip()
    if not url: return 
    while True:
        try:
            requests.get(url, timeout=10)
        except:
            pass
        time.sleep(600)


# --- Event Handlers ---

@client.on("ready")
async def on_ready(_):
    try:
        user = await client.get_me()
        print_banner()
        print(f"Logged in: {user.name}")

        from utils.state import state
        await state.initialize()

        commands_dir = os.path.join(SCRIPT_DIR, "commands")
        found_cmds = 0
        if os.path.exists(commands_dir):
            from utils.plugin_utils import load_plugin
            for f in os.listdir(commands_dir):
                if f.endswith(".py") and not f.startswith("_"):
                    if load_plugin(client, f"commands.{f[:-3]}"):
                        found_cmds += 1

        print(f"Loaded {found_cmds} plugins")

        from utils.error_reporter import ErrorReporter
        await ErrorReporter.initialize(client)
        await ErrorReporter.boot_message(client, found_cmds)

    except Exception as e:
        print(f"boot failed: {e}")


# PM Protection
from utils.pm_permit_manager import enforce_pm_protection

@client.on("message")
async def pm_protection_listener(msg: Message):
    try:
        from utils.state import BOOT_TIME
        if getattr(msg, "timestamp", 0) < BOOT_TIME:
            return
        await enforce_pm_protection(client, msg)
    except:
        pass


# --- Lifecycle ---

async def shutdown(sig: Optional[signal.Signals] = None):
    if sig:
        logger.info(f"Received {sig.name}, shutting down...")
    try:
        if client.is_connected:
            await client.stop()
    except:
        pass
    sys.exit(0)


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    async with client:
        await client.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"FATAL: {e}", exc_info=True)
        sys.exit(1)
