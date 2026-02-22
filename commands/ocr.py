# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import os
import base64
from . import *
from config import config

@astra_command(
    name="ocr",
    description="AI-powered text extraction from images.",
    category="Astra Essentials",
    aliases=["read"],
    usage="(reply to an image)",
    owner_only=False
)
async def ocr_handler(client: Client, message: Message):
    """AI OCR using Gemini."""
    try:
        if not message.has_quoted_msg or not message.quoted.is_media:
            return await smart_reply(message, " 👁️ Reply to an image to read its text.")

        status_msg = await smart_reply(message, " 👁️ *AI is reading the image...*")

        # 1. Download Media
        file_path = await client.media.download(message.quoted)
        if not file_path:
            return await status_msg.edit(" ❌ Failed to download image for OCR.")

        # 2. Use Gemini for High-Precision OCR
        # We assume Astra already has Gemini configured in config/engine
        from google import genai
        from google.genai import types
        
        api_key = getattr(config, 'GEMINI_API_KEY', None)
        if not api_key:
             return await status_msg.edit(" ❌ Gemini API Key not found in config.")

        ai_client = genai.Client(api_key=api_key)
        
        with open(file_path, "rb") as f:
            image_bytes = f.read()

        prompt = "Extract all text from this image exactly as it appears. If there is no text, say 'No text found'."
        
        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")]
        )

        extracted_text = response.text if response.text else "No text detected."

        # 3. Formatted Output
        text = (
            f"👁️ **AI OCR RESULT**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{extracted_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 *Powered by Astra AI*"
        )
        
        await status_msg.edit(text)
        
        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await smart_reply(message, f" ❌ OCR Error: {str(e)}")
        await report_error(client, e, context='OCR command failure')
