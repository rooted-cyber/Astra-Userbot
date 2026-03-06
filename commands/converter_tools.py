import os
import asyncio
import time

from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

@astra_command(name="todoc", description="Convert an image or video to a document file.", category="Tools & Utilities", aliases=["todocument"])
async def todoc_handler(client: Client, message: Message):
    """Downloads replied media and uploads it as a document."""
    if not message.has_quoted_msg or message.quoted_type not in (MessageType.IMAGE, MessageType.VIDEO):
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target image or video required.")

    status_txt = f"{UI.header('MEDIA CONVERSION')}\n{UI.mono('[ BUSY ]')} Encoding to document format..."
    status_msg = await edit_or_reply(message, status_txt)

    try:
        ext = "mp4" if message.quoted_type == MessageType.VIDEO else "jpg"
        temp_file = f"/tmp/astra_doc_conv_{int(time.time())}.{ext}"
        
        media_path = await message.quoted.download(temp_file)
        if not media_path:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Source download failed.")

        mimetype = "video/mp4" if ext == "mp4" else "image/jpeg"
        
        # In whatsapp-web.js / Astra, setting sendMediaAsDocument in options triggers document upload
        await client.send_file(
            message.chat_id, 
            temp_file, 
            caption=f"{UI.mono('[ OK ]')} Data converted to document",
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
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target document required.")

    status_txt = f"{UI.header('IMAGE EXTRACTION')}\n{UI.mono('[ BUSY ]')} Rendering document buffer..."
    status_msg = await edit_or_reply(message, status_txt)

    try:
        # Standard file path handling
        temp_file = f"/tmp/astra_img_conv_{int(time.time())}.jpg"
        
        media_path = await message.quoted.download(temp_file)
        if not media_path:
            return await status_msg.edit("❌ Failed to download document.")

        # Ensure we send it explicitly without the document flag
        await client.send_image(
            message.chat_id, 
            temp_file, 
            caption=f"{UI.mono('[ OK ]')} Data converted to image"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"{UI.mono('[ ERROR ]')} Conversion failure: {UI.mono(str(e))}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@astra_command(name="pdf2img", description="Extract images from a PDF document.", category="Tools & Utilities", aliases=["pdftoimage"])
async def pdf2img_handler(client: Client, message: Message):
    """Downloads replied PDF document and extracts all pages as images."""
    if not message.has_quoted_msg or message.quoted_type != MessageType.DOCUMENT:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target PDF document required.")

    status_txt = f"{UI.header('PDF RENDERING')}\n{UI.mono('[ BUSY ]')} Initializing OCR/Render pipeline..."
    status_msg = await edit_or_reply(message, status_txt)

    temp_pdf = f"/tmp/astra_pdf_in_{int(time.time())}.pdf"
    
    try:
        media_path = await message.quoted.download(temp_pdf)
        if not media_path:
            return await status_msg.edit("❌ Failed to download PDF document.")

        import fitz  # PyMuPDF
        
        doc = fitz.open(temp_pdf)
        num_pages = len(doc)
        
        # Batch render pages
        await status_msg.edit(f"{UI.mono('[ BUSY ]')} Processing {num_pages} sequence(s)...")
        
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
            
            await client.send_image(
                message.chat_id, 
                temp_img, 
                caption=f"{UI.mono('[ OK ]')} Page {page_num + 1}/{num_pages} rendered"
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
