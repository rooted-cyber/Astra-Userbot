import base64
import urllib.parse

import aiohttp
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="txtimg",
    description="Convert plain text into a beautiful image card.",
    category="Creative Suite",
    usage="<text>",
    is_public=True,
)
async def txtimg_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args and not message.has_quoted_msg:
        return await edit_or_reply(
            message,
            f"{UI.mono('[ ERROR ]')} Input text or quote required.\n{UI.bold('USAGE:')} {UI.mono('.txtimg <text>')}",
        )

    text = " ".join(args) if args else message.quoted.body
    status_txt = f"{UI.header('CREATIVE STUDIO')}\n{UI.mono('[ BUSY ]')} Rendering typography canvas..."
    status_msg = await edit_or_reply(message, status_txt)

    # Using a reliable free API for text-to-image
    base_url = "https://image.pollinations.ai/prompt/"
    prompt = f"A beautiful typography card with the text: '{text}'. centered, professional, clean, high resolution, soft background."
    encoded_prompt = urllib.parse.quote(prompt)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}{encoded_prompt}") as resp:
            if resp.status == 200:
                image_data = await resp.read()
                b64_data = base64.b64encode(image_data).decode("utf-8")

                media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "text_card.jpg"}
                await client.send_media(message.chat_id, media, caption=f"{UI.mono('[ OK ]')} Astra Typography Card")
                await status_msg.delete()
            else:
                await status_msg.edit(f"{UI.mono('[ ERROR ]')} Typography rendering failed.")


@astra_command(
    name="kcode",
    description="Carbon-style rendering for plain text (not just code).",
    category="Creative Suite",
    usage="<text>",
    is_public=True,
)
async def kcode_handler(client: Client, message: Message):
    """
    Uses Carbonara API but optimized for plain text descriptions.
    """
    args = extract_args(message)
    if not args and not message.has_quoted_msg:
        return await edit_or_reply(
            message, f"{UI.mono('[ ERROR ]')} Code buffer required.\n{UI.bold('USAGE:')} {UI.mono('.kcode <code>')}"
        )

    text = " ".join(args) if args else message.quoted.body
    status_txt = f"{UI.header('CARBON ENGINE')}\n{UI.mono('[ BUSY ]')} Styling premium buffer..."
    status_msg = await edit_or_reply(message, status_txt)

    url = "https://carbonara.solopov.dev/api/cook"
    payload = {
        "code": text,
        "backgroundColor": "rgba(27, 20, 41, 1)",
        "theme": "panda",  # Slick dark theme
        "language": "plain_text",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                b64_data = base64.b64encode(image_data).decode("utf-8")

                media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "kcode.jpg"}
                await client.send_media(message.chat_id, media, caption=f"{UI.mono('[ OK ]')} Astra Premium Render")
                await status_msg.delete()
            else:
                await status_msg.edit(f"{UI.mono('[ ERROR ]')} Carbon rendering failed.")
