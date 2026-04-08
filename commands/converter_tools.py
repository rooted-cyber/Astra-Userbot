import os
import asyncio
import time
import re
from typing import Dict, List
from PIL import Image, ImageSequence

from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


QUEUE_TTL_SECONDS = 15 * 60
IMG2PDF_QUEUE: Dict[str, Dict[str, object]] = {}


def _img2pdf_queue_key(message: Message) -> str:
    chat = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
    sender = str(getattr(message, "sender", "") or getattr(message, "author", "") or "me")
    return f"{chat}:{sender}"


def _cleanup_files(paths: List[str]) -> None:
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _normalize_queue_state(raw) -> Dict[str, object]:
    """Backward-compatible queue state normalization."""
    now = int(time.time())
    if isinstance(raw, list):
        return {
            "files": list(raw),
            "source_ids": set(),
            "updated_at": now,
        }

    if isinstance(raw, dict):
        files = raw.get("files", [])
        source_ids = raw.get("source_ids", set())
        updated_at = int(raw.get("updated_at", now))
        return {
            "files": list(files) if isinstance(files, list) else [],
            "source_ids": set(source_ids) if isinstance(source_ids, (set, list, tuple)) else set(),
            "updated_at": updated_at,
        }

    return {
        "files": [],
        "source_ids": set(),
        "updated_at": now,
    }


def _get_queue_state(queue_key: str, *, create: bool = False) -> Dict[str, object]:
    now = int(time.time())
    raw = IMG2PDF_QUEUE.get(queue_key)
    if raw is None:
        if not create:
            return {"files": [], "source_ids": set(), "updated_at": now}
        state = {"files": [], "source_ids": set(), "updated_at": now}
        IMG2PDF_QUEUE[queue_key] = state
        return state

    state = _normalize_queue_state(raw)
    age = now - int(state.get("updated_at", now))
    if age > QUEUE_TTL_SECONDS:
        _cleanup_files(state.get("files", []))
        state = {"files": [], "source_ids": set(), "updated_at": now}

    state["updated_at"] = now
    IMG2PDF_QUEUE[queue_key] = state
    return state


def _clear_queue_state(queue_key: str) -> None:
    state = _normalize_queue_state(IMG2PDF_QUEUE.get(queue_key))
    _cleanup_files(state.get("files", []))
    IMG2PDF_QUEUE.pop(queue_key, None)


def _pdf_frames_from_image(path: str) -> List[Image.Image]:
    frames: List[Image.Image] = []
    with Image.open(path) as src:
        if getattr(src, "is_animated", False):
            for frame in ImageSequence.Iterator(src):
                frames.append(frame.convert("RGB"))
        else:
            frames.append(src.convert("RGB"))
    return frames


def _msg_field(msg, *names):
    for name in names:
        value = getattr(msg, name, None)
        if value is not None:
            return value
    return None


def _message_id_str(msg) -> str:
    raw = _msg_field(msg, "id", "message_id", "messageId")
    if raw is None:
        return ""
    if hasattr(raw, "serialized"):
        return str(raw.serialized)
    if hasattr(raw, "_serialized"):
        return str(raw._serialized)
    return str(raw)


def _message_sender_id(msg) -> str:
    raw = _msg_field(msg, "sender", "author", "from", "from_id")
    return str(raw) if raw else ""


def _message_ts(msg) -> int:
    ts = _msg_field(msg, "timestamp", "t")
    try:
        return int(ts or 0)
    except Exception:
        return 0


def _is_image_like_message(msg) -> bool:
    mtype = str(_msg_field(msg, "quoted_type", "type", "message_type") or "").lower()
    if "image" in mtype:
        return True

    is_media = bool(getattr(msg, "is_media", False))
    if not is_media:
        return False

    mimetype = str(_msg_field(msg, "mimetype") or "").lower()
    if mimetype.startswith("image/"):
        return True

    # Document with image mime still counts for img2pdf.
    if "document" in mtype and mimetype.startswith("image/"):
        return True

    return False


def _group_id(msg):
    return _msg_field(msg, "media_group_id", "grouped_id", "groupedId", "album_id", "albumId")


async def _recent_image_cluster_fallback(client: Client, message: Message, sender_hint: str = "") -> List[Message]:
    """Fallback resolver: detect latest contiguous image cluster before command message."""
    chat_id_str = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
    anchor_id = _message_id_str(message)

    try:
        recent = await client.chat.fetch_messages(
            chat_id_str,
            limit=80,
            message_id=anchor_id if anchor_id else None,
            direction="before",
            include_anchor=False,
        )
    except Exception:
        return []

    if not recent:
        return []

    images = [m for m in recent if _is_image_like_message(m)]
    if not images:
        return []

    # Prefer sender-matching images when we have a hint.
    if sender_hint:
        sender_images = [m for m in images if _message_sender_id(m) == sender_hint]
        if sender_images:
            images = sender_images

    # Use the latest image as pivot and collect a tight time cluster (album-like burst).
    images.sort(key=_message_ts, reverse=True)
    pivot_ts = _message_ts(images[0])
    if not pivot_ts:
        # Best effort: return up to 10 latest images if timestamps are unavailable.
        return list(reversed(images[:6]))

    clustered = []
    prev_ts = pivot_ts
    for m in images:
        ts = _message_ts(m)
        if not ts:
            continue
        # Keep this fallback very tight to avoid pulling older unrelated photos.
        if abs(ts - pivot_ts) <= 75 and abs(prev_ts - ts) <= 25:
            clustered.append(m)
            prev_ts = ts
        if len(clustered) >= 12:
            break

    if not clustered:
        return []

    clustered.sort(key=_message_ts)
    return clustered


async def _resolve_img2pdf_sources(client: Client, message: Message) -> List[Message]:
    """Resolve one or more source messages (single image or album/combo images)."""
    quoted = getattr(message, "quoted", None)

    # Fallback 1: explicit quoted message fetch API, if available.
    if not quoted and hasattr(message, "get_quoted_msg"):
        try:
            quoted = await message.get_quoted_msg()
        except Exception:
            quoted = None

    if not quoted and hasattr(message, "get_quoted_message"):
        try:
            quoted = await message.get_quoted_message()
        except Exception:
            quoted = None

    # Fallback 2: resolve anchor from quoted message ID when quoted object is missing.
    if not quoted:
        qid = getattr(message, "quoted_message_id", None) or getattr(message, "quotedMessageId", None)
        if qid:
            chat_id_str = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
            try:
                around = await client.chat.fetch_messages(
                    chat_id_str, limit=10, message_id=qid, direction="after", include_anchor=True
                )
                if around:
                    qid_s = str(qid)
                    for m in around:
                        mid = _message_id_str(m)
                        if mid == qid_s or mid.endswith(qid_s):
                            quoted = m
                            break
                    if not quoted:
                        quoted = around[0]
            except Exception:
                quoted = None

    if not quoted:
        # Deep fallback: try recent cluster resolution without explicit quoted metadata.
        sender_hint = _message_sender_id(message)
        return await _recent_image_cluster_fallback(client, message, sender_hint=sender_hint)

    if quoted and _is_image_like_message(quoted):
        return [quoted]

    # Replying to album summary/card: gather nearby messages around quoted anchor.
    anchor = quoted
    if not anchor:
        return []

    chat_id_str = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
    anchor_id = getattr(anchor, "id", None)

    nearby: List[Message] = []
    if anchor_id:
        before = await client.chat.fetch_messages(
            chat_id_str, limit=25, message_id=anchor_id, direction="before", include_anchor=True
        )
        after = await client.chat.fetch_messages(
            chat_id_str, limit=25, message_id=anchor_id, direction="after", include_anchor=True
        )
        nearby = (before or []) + (after or [])

    # Deduplicate by message id preserving order.
    unique = []
    seen_ids = set()
    for msg in nearby:
        mid = str(getattr(msg, "id", ""))
        if not mid or mid in seen_ids:
            continue
        seen_ids.add(mid)
        unique.append(msg)

    if not unique:
        sender_hint = _message_sender_id(anchor) or _message_sender_id(message)
        return await _recent_image_cluster_fallback(client, message, sender_hint=sender_hint)

    g_id = _group_id(anchor)
    if g_id:
        grouped = [m for m in unique if _group_id(m) == g_id and _is_image_like_message(m)]
        if grouped:
            return grouped

    # Fallback: likely album summary body like "3 photos"; collect sender+time-clustered images.
    body = str(getattr(anchor, "body", "") or "").strip().lower()
    sender = _message_sender_id(anchor)
    anchor_ts = _message_ts(anchor)
    album_hint = bool(re.search(r"\b\d+\s+photos?\b", body))

    clustered = []
    for m in unique:
        if not _is_image_like_message(m):
            continue

        if sender and _message_sender_id(m) and _message_sender_id(m) != sender:
            continue

        ts = _message_ts(m)
        if anchor_ts and ts and abs(ts - anchor_ts) > 90:
            continue

        clustered.append(m)

    # If we detected album-style hint, allow larger grouped extraction, else single nearest image.
    if album_hint and clustered:
        return clustered

    if clustered:
        clustered.sort(key=lambda m: abs(_message_ts(m) - anchor_ts) if anchor_ts else 0)
        return [clustered[0]]

    sender_hint = _message_sender_id(anchor) or _message_sender_id(message)
    return await _recent_image_cluster_fallback(client, message, sender_hint=sender_hint)


@astra_command(
    name="img2pdf",
    description="Convert a replied image to PDF.",
    category="Tools & Utilities",
    aliases=["imgtopdf", "topdf"],
)
async def img2pdf_handler(client: Client, message: Message):
    """Convert replied image to PDF, or use queue mode: -q add, -y finalize."""
    args = [a.lower() for a in extract_args(message)]
    use_queue = "-q" in args
    finalize_queue = "-y" in args
    clear_queue = "-c" in args or "--clear" in args
    queue_key = _img2pdf_queue_key(message)

    if clear_queue:
        _clear_queue_state(queue_key)
        return await edit_or_reply(message, "img2pdf queue\nstatus: cleared")

    if finalize_queue:
        state = _get_queue_state(queue_key, create=False)
        queued_files = list(state.get("files", []))
        if not queued_files:
            return await edit_or_reply(message, "error: queue is empty, add images with .img2pdf -q")

        status_msg = await edit_or_reply(message, f"img2pdf\nstatus: building pdf from {len(queued_files)} queued image(s)")
        temp_pdf = f"/tmp/astra_img2pdf_queue_{int(time.time())}.pdf"

        try:
            frames: List[Image.Image] = []
            for path in queued_files:
                if os.path.exists(path):
                    frames.extend(_pdf_frames_from_image(path))

            if not frames:
                return await status_msg.edit("error: queue files are missing or unreadable")

            first, rest = frames[0], frames[1:]
            first.save(temp_pdf, "PDF", save_all=True, append_images=rest)

            await client.send_file(
                message.chat_id,
                temp_pdf,
                document=True,
                caption=f"done: combined {len(queued_files)} image(s) to pdf",
                reply_to=message.id,
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(f"error: img2pdf queue finalize failed\n{str(e)}")
        finally:
            _clear_queue_state(queue_key)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
        return

    source_messages = await _resolve_img2pdf_sources(client, message)
    if not source_messages:
        return await edit_or_reply(
            message,
            "error: reply to an image or album\nuse: .img2pdf (single/album) | .img2pdf -q (queue) | .img2pdf -y (finalize)",
        )

    status_msg = await edit_or_reply(message, f"img2pdf\nstatus: processing {len(source_messages)} item(s)")
    temp_inputs = []
    temp_pdf = f"/tmp/astra_img2pdf_out_{int(time.time())}.pdf"

    try:
        if use_queue:
            state = _get_queue_state(queue_key, create=True)
            files = state.get("files", [])
            source_ids = state.get("source_ids", set())
            added = 0
            for src_msg in source_messages:
                source_id = _message_id_str(src_msg)
                if source_id and source_id in source_ids:
                    continue

                media_data = await bridge_downloader.download_media(client, src_msg)
                if not media_data:
                    continue
                queue_file = f"/tmp/astra_img2pdf_queue_{int(time.time() * 1000)}_{added}.bin"
                with open(queue_file, "wb") as f:
                    f.write(media_data)
                files.append(queue_file)
                if source_id:
                    source_ids.add(source_id)
                added += 1

            state["files"] = files
            state["source_ids"] = source_ids
            state["updated_at"] = int(time.time())
            IMG2PDF_QUEUE[queue_key] = state

            if added == 0:
                return await status_msg.edit("img2pdf queue\nstatus: no new images added")

            return await status_msg.edit(
                f"img2pdf queue\nstatus: added\nitems: {len(files)}\nrun .img2pdf -y when done"
            )

        frames = []
        for idx, src_msg in enumerate(source_messages):
            media_data = await bridge_downloader.download_media(client, src_msg)
            if not media_data:
                continue
            temp_input = f"/tmp/astra_img2pdf_in_{int(time.time() * 1000)}_{idx}.bin"
            with open(temp_input, "wb") as f:
                f.write(media_data)
            temp_inputs.append(temp_input)
            frames.extend(_pdf_frames_from_image(temp_input))

        if not frames:
            return await status_msg.edit("error: no image frames found")

        first, rest = frames[0], frames[1:]
        first.save(temp_pdf, "PDF", save_all=True, append_images=rest)

        await client.send_file(
            message.chat_id,
            temp_pdf,
            document=True,
            caption="done: converted image to pdf",
            reply_to=message.id,
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"error: img2pdf failed\n{str(e)}")
    finally:
        for temp_input in temp_inputs:
            if os.path.exists(temp_input):
                os.remove(temp_input)
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)

@astra_command(name="todoc", description="Convert an image or video to a document file.", category="Tools & Utilities", aliases=["todocument"])
async def todoc_handler(client: Client, message: Message):
    """Downloads replied media and uploads it as a document."""
    if not message.has_quoted_msg or message.quoted_type not in (MessageType.IMAGE, MessageType.VIDEO):
        return await edit_or_reply(message, f"{UI.mono('error')} Target image or video required.")

    status_txt = f"{UI.header('MEDIA CONVERSION')}\n{UI.mono('processing')} Encoding to document format..."
    status_msg = await edit_or_reply(message, status_txt)

    try:
        ext = "mp4" if message.quoted_type == MessageType.VIDEO else "jpg"
        temp_file = f"/tmp/astra_doc_conv_{int(time.time())}.{ext}"
        
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('error')} Source download failed.")
        with open(temp_file, "wb") as f:
            f.write(media_data)
        media_path = temp_file

        mimetype = "video/mp4" if ext == "mp4" else "image/jpeg"
        
        # In whatsapp-web.js / Astra, setting sendMediaAsDocument in options triggers document upload
        await client.send_file(
            message.chat_id, 
            temp_file, 
            caption=f"{UI.mono('done')} Data converted to document",
            document=True
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Conversion failed: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@astra_command(name="toimg", description="Convert a document (if it's an image) to an inline image.", category="Tools & Utilities", aliases=["toimage"])
async def toimg_handler(client: Client, message: Message):
    """Downloads replied document and uploads it as an inline image."""
    if not message.has_quoted_msg or message.quoted_type != MessageType.DOCUMENT:
        return await edit_or_reply(message, f"{UI.mono('error')} Target document required.")

    status_txt = f"{UI.header('IMAGE EXTRACTION')}\n{UI.mono('processing')} Rendering document buffer..."
    status_msg = await edit_or_reply(message, status_txt)

    try:
        # Standard file path handling
        temp_file = f"/tmp/astra_img_conv_{int(time.time())}.jpg"
        
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit("❌ Failed to download document.")
        with open(temp_file, "wb") as f:
            f.write(media_data)
        media_path = temp_file

        # Ensure we send it explicitly without the document flag
        await client.send_file(
            message.chat_id, 
            temp_file, 
            caption=f"{UI.mono('done')} Data converted to image"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Conversion failure: {UI.mono(str(e))}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@astra_command(name="pdf2img", description="Extract images from a PDF document.", category="Tools & Utilities", aliases=["pdftoimage"])
async def pdf2img_handler(client: Client, message: Message):
    """Downloads replied PDF document and extracts all pages as images."""
    if not message.has_quoted_msg or message.quoted_type != MessageType.DOCUMENT:
        return await edit_or_reply(message, f"{UI.mono('error')} Target PDF document required.")

    status_txt = f"{UI.header('PDF RENDERING')}\n{UI.mono('processing')} Starting OCR/Render pipeline..."
    status_msg = await edit_or_reply(message, status_txt)

    temp_pdf = f"/tmp/astra_pdf_in_{int(time.time())}.pdf"
    
    try:
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit("❌ Failed to download PDF document.")
        with open(temp_pdf, "wb") as f:
            f.write(media_data)
        media_path = temp_pdf

        import fitz  # PyMuPDF
        
        doc = fitz.open(temp_pdf)
        num_pages = len(doc)
        
        # Batch render pages
        await status_msg.edit(f"{UI.mono('processing')} Processing {num_pages} sequence(s)...")
        
        # Determine DPI, usually 150-300 is good, keeping it moderate to save time/bandwidth
        zoom_x = 2.0  # horizontal zoom
        zoom_y = 2.0  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)

        # Batch send pages
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            
            temp_img = f"/tmp/astra_pdf_out_{int(time.time())}_page_{page_num+1}.jpg"
            pix.save(temp_img)
            
            await client.send_file(
                message.chat_id, 
                temp_img, 
                caption=f"{UI.mono('done')} Page {page_num + 1}/{num_pages} rendered"
            )
            
            if os.path.exists(temp_img):
                os.remove(temp_img)
                
            # Prevent rate limiting on large PDFs
            if page_num < num_pages - 1:
                time.sleep(0.5)

        doc.close()
        await status_msg.delete()

    except ImportError:
        await status_msg.edit("❌ PyMuPDF (`fitz`) is not installed. Run `pip install PyMuPDF`.")
    except Exception as e:
        await status_msg.edit(f"❌ Extraction failed: {str(e)}")
    finally:
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
