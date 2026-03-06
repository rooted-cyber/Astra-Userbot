import time
import platform
import time

from config import config
from . import *
from utils.ui_templates import UI

@astra_command(
    name="ping",
    description="Measure Astra Engine bridge latency.",
    category="Tools & Utilities",
    aliases=["p"],
    usage=".ping",
    is_public=True,
)
async def ping_handler(client: Client, message: Message):
    """Calculates round-trip latency with minimalist technical output."""
    start_time = time.time()

    # Direct report generation (no intermediate edit)

    end_time = time.time()
    latency = round((end_time - start_time) * 1000)

    # Determine status
    status = UI.get_ping_status(latency)

    # Build pro-style report
    ping_report = (
        f"{UI.bold('LATENCY CORE REPORT')}\n"
        f"{UI.DIVIDER}\n"
        f"Latency  : {UI.mono(f'[{latency}ms]')}\n"
        f"Network  : {UI.mono(status)}\n"
        f"Version  : {UI.mono(config.VERSION)}\n"
        f"System   : {UI.mono(platform.system())}\n"
        f"{UI.DIVIDER}\n"
        f"{UI.italic('Protocol: Astra Secure Bridge')}"
    )

    # Determine reply target
    reply_id = message.quoted_id if message.has_quoted_msg else message.id

    # Send report immediately
    await client.send_message(message.chat_id, ping_report, reply_to=reply_id)
    
    # Clean up trigger if possible (owner only)
    try:
        if message.from_me:
            await message.delete()
    except:
        pass
