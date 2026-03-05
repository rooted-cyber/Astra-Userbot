import base64
import io
import textwrap

from PIL import Image, ImageDraw, ImageFont
from utils.bridge_downloader import bridge_downloader
from utils.helpers import handle_command_error

from . import *


@astra_command(
    name="mm",
    description="Create a meme from an image. Use | to separate top and bottom text.",
    category="Tools & Utilities",
    usage="(reply to image) Top Text | Bottom Text",
    is_public=True,
)
async def meme_maker_handler(client: Client, message: Message):
    """Meme maker plugin."""
    try:
        quoted = message.quoted if message.has_quoted_msg else None
        target = quoted if quoted and quoted.is_media else (message if message.is_media else None)

        if not target or target.type != MessageType.IMAGE:
            return await smart_reply(message, "✨ Reply to an image to make a meme.")

        text = message.text_after_command
        if not text:
            return await smart_reply(message, "✨ Provide text for the meme. Example: `.mm Top Text | Bottom Text`")

        top_text, bottom_text = "", ""
        if "|" in text:
            parts = text.split("|")
            top_text = parts[0].strip().upper()
            bottom_text = parts[1].strip().upper()
        else:
            top_text = text.strip().upper()

        status_msg = await smart_reply(message, "✨ **Generating meme...**")

        # Download image
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit("❌ Failed to download image.")

        # Process with PIL
        img = Image.open(io.BytesIO(media_data)).convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Load font
        font_path = "/Users/paman7647/ASTRAUB/astra_userbot_test/utils/logos/font1.ttf"
        
        def get_font_size(text, max_width, max_height):
            size = int(height / 8)
            font = ImageFont.truetype(font_path, size)
            while font.getlength(text) > max_width and size > 10:
                size -= 2
                font = ImageFont.truetype(font_path, size)
            return font

        def draw_text(text, position):
            if not text:
                return
            
            # Wrap text if too long
            wrapped = textwrap.wrap(text, width=20)
            
            y_offset = 0
            for line in wrapped:
                font = get_font_size(line, width * 0.9, height / 10)
                # Use textbbox instead of deprecated textsize
                bbox = draw.textbbox((0, 0), line, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                
                x = (width - w) / 2
                y = position[1] + y_offset if position[0] == "top" else (height - h - 10 - (len(wrapped)-1-y_offset/h)*h)
                
                if position[0] == "bottom":
                     y = position[1] - h - y_offset
                
                # Draw outline
                for adj in range(-2, 3):
                    for adj2 in range(-2, 3):
                        draw.text((x + adj, y + adj2), line, font=font, fill="black")
                
                draw.text((x, y), line, font=font, fill="white")
                y_offset += h + 5

        # Draw top and bottom text
        if top_text:
            draw_text(top_text, ("top", 20))
        if bottom_text:
            # For bottom text, we calculate from the bottom
            wrapped_bottom = textwrap.wrap(bottom_text, width=15)
            total_h = 0
            for line in wrapped_bottom:
                font = get_font_size(line, width * 0.9, height / 10)
                bbox = draw.textbbox((0, 0), line, font=font)
                total_h += (bbox[3] - bbox[1]) + 5
            
            draw_text(bottom_text, ("bottom", height - 20))

        # Save to buffer
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=90)
        b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

        media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "meme.jpg"}
        await client.send_media(message.chat_id.serialized, media, caption="✨ Created with **Astra Meme Maker**")
        await status_msg.delete()

    except Exception as e:
        await handle_command_error(client, message, e, context="Meme maker failure")
