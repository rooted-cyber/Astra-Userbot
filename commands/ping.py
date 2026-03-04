
import time
import asyncio
import platform
from config import config
from . import *

@astra_command(
    name="ping",
    description="Description: Measure the round-trip latency (RTT) between the Astra engine and WhatsApp's globally distributed servers. This command performs a real-time connectivity test to ensure optimal responsiveness and identifies potential network bottlenecks.\nSyntax: .ping\nExample: .ping",
    category="Tools & Utilities",
    aliases=["p"],
    usage=".ping (checks latency)",
    is_public=True
)
async def ping_handler(client: Client, message: Message):
    """Calculates round-trip latency with descriptive system context."""
    try:
        start_time = time.time()
        
        # First edit without delay
        status_msg = await message.reply("📡 **ASTRA CONNECTIVITY TEST**\n━━━━━━━━━━━━━━━━━━━━\n🔍 **Status:** `Measuring...`")
        
        end_time = time.time()
        latency = round((end_time - start_time) * 1000)
        
        # Determine status level
        status = "Excellent" if latency < 200 else "Good" if latency < 500 else "Average"
        
        # Final result with descriptive formatting
        descriptive_ping = (
            "🏓 **PONG!** 🚀\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 **Latency:** `{latency}ms`\n"
            f"🛰️ **Network:** `{status}`\n"
            f"🏷️ **Version:** `{config.VERSION}` (**{config.VERSION_NAME}**)\n"
            f"⚙️ **System:** `{platform.system()} ({platform.release()})`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✨ *Astra Engine is in peak form.*"
        )
        
        # Second edit with manual delay
        time.sleep(0.5)
        await status_msg.edit(descriptive_ping)

    except Exception as e:
        await smart_reply(message, " ⚠️ Connectivity check failed.")
        await report_error(client, e, context='Ping command failure')
