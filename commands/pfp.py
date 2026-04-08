import io
import aiohttp
from PIL import Image
from astra import Client, Message
from utils.plugin_utils import astra_command, extract_args
from utils.helpers import edit_or_reply, send_bytes_media
from utils.ui_templates import UI


INLINE_PFP_URL_JS = """
async (idRef) => {
    try {
        const Store = window.Astra.initializeEngine();

        const toIdString = (ref) => {
            if (!ref) return null;
            if (typeof ref === 'string') return ref;
            if (typeof ref === 'object') {
                if (typeof ref._serialized === 'string') return ref._serialized;
                if (typeof ref.serialized === 'string') return ref.serialized;
                if (typeof ref.id === 'string') return ref.id;
                if (ref.id && typeof ref.id._serialized === 'string') return ref.id._serialized;
            }
            return String(ref);
        };

        let id = toIdString(idRef);
        if (!id) return { error: 'invalid_id' };

        const normalize = (v) => {
            if (!v) return null;
            let s = String(v).trim();
            if (!s) return null;
            if (!s.includes('@')) {
                s = `${s.replace(/[^0-9]/g, '')}@c.us`;
            }
            return s;
        };

        id = normalize(id);
        if (!id) return { error: 'normalized_id_empty' };

        const getChatById = Store.Chat?.get || Store.Chat?.find;
        let chat = null;
        if (getChatById) {
            try {
                chat = await getChatById.call(Store.Chat, id);
            } catch (e) {}
        }

        let contact = null;
        if (Store.Contact) {
            contact = Store.Contact.get ? Store.Contact.get(id) : null;
            if (!contact && Store.Contact.find) {
                try { contact = await Store.Contact.find(id); } catch (e) {}
            }
        }

        const picGetter = Store.ProfilePic?.profilePicFind || Store.ProfilePic?.find;
        if (picGetter) {
            try {
                const wid = (chat && chat.id) || (contact && contact.id) || id;
                const picObj = await picGetter.call(Store.ProfilePic, wid);
                const direct = picObj?.eurl || picObj?.url || picObj?.imgFull || picObj?.img;
                if (direct) return { url: direct, source: 'profilepic' };
            } catch (e) {}
        }

        // Last fallback: try Contact model direct fields.
        const direct = contact?.profilePicThumbObj?.eurl || contact?.profilePicThumbObj?.imgFull || contact?.profilePicThumbObj?.img;
        if (direct) return { url: direct, source: 'contact_model' };

        return { error: 'not_found' };
    } catch (e) {
        return { error: String(e) };
    }
}
"""


def _serialize_contact_id(raw) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw

    for attr in ("serialized", "_serialized", "id"):
        v = getattr(raw, attr, None)
        if isinstance(v, str) and v:
            return v

    nested = getattr(raw, "id", None)
    for attr in ("serialized", "_serialized", "id"):
        v = getattr(nested, attr, None) if nested is not None else None
        if isinstance(v, str) and v:
            return v

    return str(raw)

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
        contact_id = _serialize_contact_id(message.quoted.sender)
    else:
        args = extract_args(message)
        if args:
            num = args[0].replace("@", "").replace("+", "").replace(" ", "")
            contact_id = f"{num}@c.us" if "@" not in num else num
        else:
            contact_id = _serialize_contact_id(message.chat_id)

    contact_id = _serialize_contact_id(contact_id)

    status_msg = await edit_or_reply(message, f"{UI.mono('processing')} Accessing profile assets...")

    try:
        url = None
        try:
            # Primary API path (expects serialized string contactId).
            url = await client.api.get_profile_pic_url(contact_id)
        except Exception:
            url = None

        if not url:
            # JS fallback path for engine/API edge cases.
            page = client.browser.page if getattr(client, "browser", None) else None
            if page:
                result = await page.evaluate(INLINE_PFP_URL_JS, contact_id)
                if isinstance(result, dict):
                    url = result.get("url")

        if not url:
            return await status_msg.edit(f"{UI.mono('error')} Asset inaccessible (Privacy Restrict).")

        # Download
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    return await status_msg.edit(f"{UI.mono('error')} Image fetch failed (HTTP {resp.status}).")
                
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

        await send_bytes_media(
            client,
            message.chat_id,
            img_data,
            filename=f"pfp_{contact_id.split('@')[0]}.jpg",
            mode="photo",
            caption=f"{UI.header('ASTRA PFP PREMIUM')}\nTarget: {UI.mono(contact_id)}",
            reply_to=message.id
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Retrieval failure: {UI.mono(str(e))}")
