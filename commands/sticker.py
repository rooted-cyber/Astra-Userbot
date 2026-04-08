import base64
import io
import time

from PIL import Image
from utils.bridge_downloader import bridge_downloader

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="sticker",
    description="Convert an image or video to a sticker.",
    category="Tools & Utilities",
    aliases=["s", "stkr"],
    usage="(reply to image/video)",
    is_public=True,
)
async def sticker_handler(client: Client, message: Message):
    """Sticker creation plugin."""
    if not message.has_quoted_msg and not message.is_media:
        return await edit_or_reply(message, f"{UI.mono('error')} Target media required (image/video).")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Converting to sticker...")

    # Download media via high-reliability Bridge
    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download media.")

    b64_data = base64.b64encode(media_data).decode("utf-8")

    # Send as sticker
    await client.media.send_sticker(
        str(message.chat_id),
        b64_data,
        reply_to=message.id,
    )

    await status_msg.delete()


@astra_command(
    name="kang",
    description="Clone a sticker or convert an image/video to a high-quality sticker.",
    category="Tools & Utilities",
    aliases=["k"],
    usage="(reply to media)",
    is_public=True,
)
async def kang_handler(client: Client, message: Message):
    """Advanced sticker cloning/creation."""
    if not message.has_quoted_msg and not message.is_media:
        return await edit_or_reply(message, f"{UI.mono('error')} Target media required (sticker/image/video).")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Kanging media segment...")

    # Download media
    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download media.")

    # Process with PIL for high quality (512x512 transparency)
    img = Image.open(io.BytesIO(media_data)).convert("RGBA")

    # Upscale or downscale precisely to fit 512x512 bounds maximally
    ratio = 512.0 / max(img.size)
    new_sizes = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_sizes, Image.Resampling.LANCZOS)

    # Create a 512x512 transparent canvas
    new_img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    # Center the fitted image
    new_img.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2))

    # Save to buffer
    out_buffer = io.BytesIO()
    new_img.save(out_buffer, format="WebP", lossless=True, quality=90)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

    # Send as sticker
    await client.media.send_sticker(
        str(message.chat_id),
        b64_data,
        reply_to=message.id,
    )

    await status_msg.delete()


@astra_command(
    name="stkrinfo",
    description="Get metadata about a sticker.",
    category="Tools & Utilities",
    usage="(reply to sticker)",
    is_public=True,
)
async def stkrinfo_handler(client: Client, message: Message):
    """Extract sticker metadata."""
    # Check if it's a sticker or has a quoted sticker
    is_sticker = message.type == MessageType.STICKER
    has_quoted_sticker = message.has_quoted_msg and message.quoted_type == MessageType.STICKER

    if not is_sticker and not has_quoted_sticker:
        return await edit_or_reply(message, f"{UI.mono('error')} Reply to a sticker to fetch metadata.")

    info = f"{UI.header('STICKER METADATA')}\n"
    info += f"ID     : {UI.mono(message.id)}\n"
    info += f"Mimetype : {UI.mono(message.mimetype or 'image/webp')}\n"
    if message.size:
        info += f"Size   : {UI.mono(f'{message.size // 1024} KB')}\n"
    info += f"Time   : {UI.mono(time.strftime('%H:%M:%S', time.localtime(message.timestamp)))}\n"

    await edit_or_reply(message, info)


@astra_command(
    name="stoi",
    description="Convert a sticker to an image.",
    category="Tools & Utilities",
    aliases=["toimage"],
    usage="(reply to sticker)",
    is_public=True,
)
async def stoi_handler(client: Client, message: Message):
    """Convert sticker to image."""
    is_sticker = message.type == MessageType.STICKER
    has_quoted_sticker = message.has_quoted_msg and message.quoted_type == MessageType.STICKER

    if not is_sticker and not has_quoted_sticker:
        return await edit_or_reply(message, f"{UI.mono('error')} Reply to a sticker for image conversion.")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Stripping sticker layer...")

    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download sticker.")

    # Convert WebP to JPEG/PNG and Upscale
    img = Image.open(io.BytesIO(media_data)).convert("RGB")
    
    # Upscale by 2x for high-quality viewing
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    
    out_buffer = io.BytesIO()
    img.save(out_buffer, format="JPEG", quality=100)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "sticker.jpg"}
    await client.send_photo(str(message.chat_id), media, caption=f"{UI.mono('done')} Converted from sticker segment.")
    await status_msg.delete()


@astra_command(
    name="getstkr",
    description="Download a sticker as a file.",
    category="Tools & Utilities",
    usage="(reply to sticker)",
    is_public=True,
)
async def getstkr_handler(client: Client, message: Message):
    """Download sticker file."""
    is_sticker = message.type == MessageType.STICKER
    has_quoted_sticker = message.has_quoted_msg and message.quoted_type == MessageType.STICKER

    if not is_sticker and not has_quoted_sticker:
        return await edit_or_reply(message, f"{UI.mono('error')} Reply to a sticker to export file.")

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Fetching sticker binary...")

    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download sticker.")

    b64_data = base64.b64encode(media_data).decode("utf-8")
    media = {"mimetype": "image/webp", "data": b64_data, "filename": "sticker.webp"}

    await client.send_document(str(message.chat_id), media)
    await status_msg.delete()


@astra_command(
    name="tiny",
    description="Create a tiny sticker (centered image).",
    category="Tools & Utilities",
    usage="(reply to image)",
    is_public=True,
)
async def tiny_handler(client: Client, message: Message):
    """Tiny sticker plugin - centered on 512x512 canvas."""
    await kang_handler(client, message)
