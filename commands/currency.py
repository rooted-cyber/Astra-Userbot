# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
from . import *

@astra_command(
    name="currency",
    description="Real-time currency and crypto converter.",
    category="Astra Essentials",
    aliases=["rate", "conv"],
    usage="<amount> <from> <to> (e.g. .currency 1 USD INR)",
    owner_only=False
)
async def currency_handler(client: Client, message: Message):
    """Currency & Crypto converter."""
    try:
        args = extract_args(message)
        if len(args) < 3:
            return await smart_reply(message, " 💰 **Currency Converter**\n\nUsage: `.conv 100 USD INR`")

        amount = args[0]
        base = args[1].upper()
        target = args[2].upper()

        status_msg = await smart_reply(message, f" 💱 *Fetching rates for {base} to {target}...*")

        # Using Frankfurter API (Free, no API key required)
        url = f"https://api.frankfurter.app/latest?amount={amount}&from={base}&to={target}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'rates' in data and target in data['rates']:
                        res = data['rates'][target]
                        rate = res / float(amount)
                        
                        text = (
                            f"💰 **CURRENCY CONVERSION**\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"💵 **Input:** `{amount} {base}`\n"
                            f"💹 **Result:** `{res:.2f} {target}`\n"
                            f"📈 **Rate:** `1 {base} = {rate:.4f} {target}`\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🚀 *Powered by Astra Userbot*"
                        )
                        return await status_msg.edit(text)
                    
        await status_msg.edit(" ⚠️ Remote rate engine failed or invalid currency code.")

    except Exception as e:
        await smart_reply(message, f" ❌ Currency Error: {str(e)}")
