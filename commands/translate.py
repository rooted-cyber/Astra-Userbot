# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
from urllib.parse import quote
from . import *

@astra_command(
    name="tr",
    description="Translate text to another language.",
    category="Core Tools",
    aliases=["translate"],
    usage="<lang_code> [text] (or reply to a message)",
    is_public=True
)
async def translate_handler(client: Client, message: Message):
    """Translation plugin using Google Translate API."""
    args = extract_args(message)
    
    # Defaults
    dest_lang = "en"
    text_to_translate = ""
    
    if message.has_quoted_msg:
        # If replying, the first arg is the target language
        dest_lang = args[0] if args else "en"
        quoted = await message.get_quoted_msg()
        text_to_translate = quoted.body
    elif len(args) >= 2:
        # .tr hi hello world -> target: hi, text: hello world
        dest_lang = args[0]
        text_to_translate = " ".join(args[1:])
    elif len(args) == 1:
        # .tr hello -> target: en (default), text: hello
        text_to_translate = args[0]
    else:
        return await smart_reply(message, "❌ **Usage:** `.tr <lang_code> <text>` or reply with `.tr <lang_code>`")

    status_msg = await smart_reply(message, f"🌏 **Translating to:** `{dest_lang}`...")

    try:
        # Google Translate mobile API (no key required for small requests)
        api_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={dest_lang}&dt=t&q={quote(text_to_translate)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    translated_text = "".join([part[0] for part in data[0]])
                    src_lang = data[2]
                    
                    text = (
                        f"🌏 **TRANSLATION ENGINE**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📥 **From:** `{src_lang.upper()}`\n"
                        f"📤 **To:** `{dest_lang.upper()}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{translated_text}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🚀 *Powered by Astra*"
                    )
                    return await status_msg.edit(text)
                
        await status_msg.edit("⚠️ Translation service is currently unavailable.")

    except Exception as e:
        await status_msg.edit(f"❌ **Translation Error:** {str(e)}")
