import io
import base64
import aiohttp
from PIL import Image
from astra import Client, Message
from utils.plugin_utils import astra_command, extract_args
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

@astra_command(
    name="pfp",
    description="Download and upscale a contact's profile picture.",
    category="Tools & Utilities",
    aliases=["dp", "profilepic"],
    usage="[@user or reply]",
    is_public=True,
)
async def pfp_premium_handler(client: Client, message: Message):
    """Premium PFP Downloader with Lanczos upscaling."""
    contact_id = None

    if message.has_quoted_msg and message.quoted:
        contact_id = message.quoted.sender
    else:
        args = extract_args(message)
        if args:
            num = args[0].replace("@", "").replace("+", "").replace(" ", "")
            contact_id = f"{num}@c.us" if "@" not in num else num
        else:
            contact_id = message.chat_id

    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Accessing profile assets...")

    try:
        url = await client.api.get_profile_pic_url(contact_id)
        if not url:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Asset inaccessible (Privacy Restrict).")

        # Download
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Image fetch failed (HTTP {resp.status}).")
                
                img_data = await resp.read()

        # Premium Upscaling (LANCZOS)
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.width < 1080:
                scale = 1080 / img.width
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=95)
            img_data = output.getvalue()
        except Exception as upscale_err:
            # Fallback to original if PIL fails
            pass

        b64_data = base64.b64encode(img_data).decode("utf-8")
        media = {
            "mimetype": "image/jpeg",
            "data": b64_data,
            "filename": f"pfp_{contact_id.split('@')[0]}.jpg"
        }

        await client.send_photo(
            message.chat_id, 
            media, 
            caption=f"{UI.header('ASTRA PFP PREMIUM')}\nTarget: {UI.mono(contact_id)}",
            reply_to=message.id
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Retrieval failure: {UI.mono(str(e))}")
