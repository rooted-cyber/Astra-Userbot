# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import os
import aiohttp
from . import *

@astra_command(
    name="ocr",
    description="Free text extraction from images (Non-AI).",
    category="Astra Essentials",
    aliases=["read"],
    usage="(reply to an image)",
    owner_only=False
)
async def ocr_handler(client: Client, message: Message):
    """Free OCR using OCR.space API."""
    file_path = None
    try:
        if not message.has_quoted_msg or not message.quoted.is_media:
            return await smart_reply(message, " 👁️ Reply to an image to read its text.")

        status_msg = await smart_reply(message, " 👁️ *Reading image text...*")

        # 1. Download Media
        file_path = await client.media.download(message.quoted)
        if not file_path:
            return await status_msg.edit(" ❌ Failed to download image for OCR.")

        # 2. OCR.space Integration (Free Tier)
        # Using the official free API endpoint
        url = "https://api.ocr.space/parse/image"
        
        # We use a public free key or allow user to provide one. 
        # Defaulting to a common free key if not in config.
        api_key = getattr(config, 'OCR_API_KEY', 'helloworld') 

        data = aiohttp.FormData()
        data.add_field('apikey', api_key)
        data.add_field('language', 'eng')
        data.add_field('file', open(file_path, 'rb'))

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    return await status_msg.edit(f" ❌ API Error: {response.status}")
                
                result = await response.json()

        # Parse Results
        if result.get('OCRExitCode') == 1:
            parsed_results = result.get('ParsedResults', [])
            extracted_text = parsed_results[0].get('ParsedText', '').strip() if parsed_results else ""
            
            if not extracted_text:
                extracted_text = "No text detected in the image."
        else:
            error_msg = result.get('ErrorMessage', ['Unknown API error'])[0]
            return await status_msg.edit(f" ❌ OCR Engine Error: {error_msg}")

        # 3. Formatted Output
        text = (
            f"👁️ **FREE OCR RESULT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{extracted_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 *Powered by Astra Engine (Free)*"
        )
        
        await status_msg.edit(text)

    except Exception as e:
        await smart_reply(message, f" ❌ OCR Error: {str(e)}")
        await report_error(client, e, context='Free OCR command failure')
    finally:
        # Cleanup
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
