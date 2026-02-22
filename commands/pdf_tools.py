# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import os
from . import *

@astra_command(
    name="pdf",
    description="Convert an image to a PDF document.",
    category="Astra Essentials",
    aliases=["topdf", "img2pdf"],
    usage="(reply to an image)",
    owner_only=False
)
async def pdf_handler(client: Client, message: Message):
    """Image to PDF converter."""
    try:
        if not message.has_quoted_msg or not message.quoted.is_media:
            return await smart_reply(message, " 📄 Reply to an image to convert it into a PDF.")

        status_msg = await smart_reply(message, " 📂 *Converting image to PDF...*")

        # 1. Download Media
        file_path = await client.media.download(message.quoted)
        if not file_path:
            return await status_msg.edit(" ❌ Failed to download image.")

        pdf_path = file_path.rsplit('.', 1)[0] + ".pdf"

        # 2. Convert using Pillow
        try:
            from PIL import Image
            img = Image.open(file_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(pdf_path, "PDF", resolution=100.0)
        except ImportError:
            return await status_msg.edit(" ❌ `Pillow` library is missing. Run `.update` or install it manually.")
        except Exception as conversion_error:
            return await status_msg.edit(f" ❌ Conversion failed: {str(conversion_error)}")

        # 3. Upload Document
        media = {
            "mimetype": "application/pdf",
            "filename": os.path.basename(pdf_path),
            "data": open(pdf_path, "rb").read() # Simple upload if file is small
        }
        
        # Using send_media bridge
        await client.send_media(message.chat_id, media, caption="📄 **Generated PDF Document**")
        await status_msg.delete()

        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)

    except Exception as e:
        await smart_reply(message, f" ❌ PDF Error: {str(e)}")
