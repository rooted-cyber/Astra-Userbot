# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import json
from utils.state import state

@astra_command(
    name="db",
    description="🛠️ Advanced Database & State Manager. Directly manipulate bot memory.",
    category="Developer Tools",
    usage="set <key> <value> | get <key> | list | del <key>",
    owner_only=True
)
async def db_tool_handler(client: Client, message: Message):
    """Developer tool for real-time state and database manipulation."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, f"❌ **Usage:** `{state.get_prefix()}db <set/get/list/del> [args]`")

    sub = args[0].lower()

    # 1. DB SET
    if sub == "set" and len(args) >= 3:
        key = args[1]
        raw_val = " ".join(args[2:])
        # Try to parse as JSON for complex types, fallback to string
        try:
            val = json.loads(raw_val)
        except:
            val = raw_val
            
        state.set_config(key, val)
        return await smart_reply(message, f"✅ **DB Update:** `{key}` set to `{val}`")

    # 2. DB GET
    elif sub == "get" and len(args) >= 2:
        key = args[1]
        val = state.get_config(key)
        if val is None:
            # Check top-level state too
            val = state.state.get(key, "Not Found")
            
        return await smart_reply(message, f"🔎 **Key:** `{key}`\n📦 **Value:** `{val}`")

    # 3. DB LIST
    elif sub == "list":
        configs = state.get_all_configs()
        if not configs:
            return await smart_reply(message, "📂 **DB:** No custom overrides found.")
        
        list_text = "📂 **DATABASE OVERRIDES**\n━━━━━━━━━━━━━━━━━━━━\n"
        for k, v in configs.items():
            list_text += f"🔹 `{k}`: `{v}`\n"
        return await smart_reply(message, list_text)

    # 4. DB DELETE
    elif sub in ["del", "delete", "rm"] and len(args) >= 2:
        key = args[1]
        if key in state.state["configs"]:
            del state.state["configs"][key]
            from utils.database import db as db_core
            asyncio.create_task(db_core.set("configs", state.state["configs"]))
            return await smart_reply(message, f"🗑️ **DB:** Deleted override `{key}`.")
        return await smart_reply(message, f"❌ **DB:** Override `{key}` not found.")

    return await smart_reply(message, "❌ Invalid sub-command. Use `set`, `get`, `list`, or `del`.")

@astra_command(
    name="setcfg",
    description="⚙️ Manage bot configuration dynamically.",
    category="System & Bot",
    usage="<key> <value>",
    owner_only=True
)
async def setcfg_handler(client: Client, message: Message):
    """User-friendly frontend for dynamic configuration."""
    args = extract_args(message)
    if len(args) < 2:
        # Show help if no args
        help_text = (
            "⚙️ **DYNAMIC CONFIGURATION**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Common Keys:**\n"
            "🔹 `ALIVE_IMG`: URL or local path for .alive\n"
            "🔹 `BOT_NAME`: Your custom bot brand name\n"
            "🔹 `COMMAND_PREFIX`: Change prefix instantly\n\n"
            f"**Usage:** `{state.get_prefix()}setcfg <key> <value>`"
        )
        return await smart_reply(message, help_text)

    key = args[1].upper()
    val = " ".join(args[2:])
    
    # Logic for specific keys
    if key == "COMMAND_PREFIX":
        state.set_prefix(val)
    else:
        state.set_config(key, val)
        
    await smart_reply(message, f"✨ **Config Updated:** `{key}` is now `{val}`")
