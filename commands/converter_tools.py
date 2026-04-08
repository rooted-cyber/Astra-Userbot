import os
import asyncio
import time
from typing import Dict, List
from PIL import Image, ImageSequence

from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


IMG2PDF_QUEUE: Dict[str, List[str]] = {}


def _img2pdf_queue_key(message: Message) -> str:
    sender = str(getattr(message, "sender", "") or getattr(message, "author", "") or "me")
    return f"{message.chat_id}:{sender}"


def _pdf_frames_from_image(path: str) -> List[Image.Image]:
    frames: List[Image.Image] = []
    with Image.open(path) as src:
        if getattr(src, "is_animated", False):
            for frame in ImageSequence.Iterator(src):
                frames.append(frame.convert("RGB"))
        else:
            frames.append(src.convert("RGB"))
    return frames


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
    queue_key = _img2pdf_queue_key(message)

    if finalize_queue:
        queued_files = IMG2PDF_QUEUE.get(queue_key, [])
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
            for path in queued_files:
                if os.path.exists(path):
                    os.remove(path)
            IMG2PDF_QUEUE.pop(queue_key, None)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
        return

    if not message.has_quoted_msg or message.quoted_type not in (MessageType.IMAGE, MessageType.DOCUMENT):
        return await edit_or_reply(
            message,
            "error: reply to an image\nuse: .img2pdf (single) | .img2pdf -q (queue) | .img2pdf -y (finalize)",
        )

    status_msg = await edit_or_reply(message, "img2pdf\nstatus: converting")
    temp_input = f"/tmp/astra_img2pdf_in_{int(time.time())}.bin"
    temp_pdf = f"/tmp/astra_img2pdf_out_{int(time.time())}.pdf"

    try:
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit("error: failed to download media")

        with open(temp_input, "wb") as f:
            f.write(media_data)

        if use_queue:
            queue_file = f"/tmp/astra_img2pdf_queue_{int(time.time() * 1000)}.bin"
            with open(queue_file, "wb") as f:
                f.write(media_data)
            IMG2PDF_QUEUE.setdefault(queue_key, []).append(queue_file)
            return await status_msg.edit(
                f"img2pdf queue\nstatus: added\nitems: {len(IMG2PDF_QUEUE[queue_key])}\nrun .img2pdf -y when done"
            )

        frames = _pdf_frames_from_image(temp_input)
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
