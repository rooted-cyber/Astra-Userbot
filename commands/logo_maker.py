import base64
import io
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI
import time
import urllib.request

# Configuration
LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)


@astra_command(
    name="logo",
    description="Create a beautiful logo with local professional backgrounds.",
    category="Creative Suite",
    usage="<text>",
    is_public=True,
)
async def logo_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " Usage: `.logo MyName`")

    text = " ".join(args)
    status_msg = await edit_or_reply(message, " Processing...")

    # 1. Pick a random local background (Prefer manually added bg1, bg2, etc.)
    bg_files = [f for f in os.listdir(LOGOS_DIR) if f.startswith("bg") and f.endswith((".jpg", ".jpeg", ".png"))]
    if not bg_files:
        bg_files = [f for f in os.listdir(LOGOS_DIR) if f.endswith((".jpg", ".jpeg", ".png"))]

    if not bg_files:
        default_bg_path = os.path.join(LOGOS_DIR, "default_bg.jpg")
        if not os.path.exists(default_bg_path):
            try:
                urllib.request.urlretrieve("https://images.unsplash.com/photo-1557683316-973673baf926?q=80&w=1024&auto=format&fit=crop", default_bg_path)
            except:
                pass
        if os.path.exists(default_bg_path):
            try:
                bg_path = default_bg_path
                img = Image.open(bg_path).convert("RGB")
                img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            except:
                img = Image.new("RGB", (1024, 1024), color=(15, 12, 25))
        else:
            img = Image.new("RGB", (1024, 1024), color=(15, 12, 25))
    else:
        bg_path = os.path.join(LOGOS_DIR, random.choice(bg_files))
        try:
            img = Image.open(bg_path).convert("RGB")
            img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        except:
            img = Image.new("RGB", (1024, 1024), color=(15, 12, 25))

    # 2. Process Image (Blur & Darken for premium text readability)
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    # Semi-transparent dark overlay for high contrast
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 130))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # 3. Draw Text
    draw = ImageDraw.Draw(img)

    # Stylized Font Selection: Pick a random font from font1.ttf to font5.ttf
    available_fonts = [f for f in os.listdir(LOGOS_DIR) if f.startswith("font") and f.endswith(".ttf")]
    if not available_fonts:
        default_font_path = os.path.join(LOGOS_DIR, "default_font.ttf")
        if not os.path.exists(default_font_path):
            try:
                urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf", default_font_path)
            except:
                pass
        font_paths = [default_font_path] if os.path.exists(default_font_path) else [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "arial.ttf",
        ]
    else:
        font_paths = [os.path.join(LOGOS_DIR, f) for f in available_fonts]
        random.shuffle(font_paths)  # Randomized style each time

    font = None
    for p in font_paths:
        try:
            # Increased font size for a more premium, high-impact look
            font = ImageFont.truetype(p, 180)
            break
        except:
            continue

    if not font:
        font = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((1024 - w) / 2, (1024 - h) / 2), text, font=font, fill=(255, 255, 255))

    # 4. Save & Send
    out_buffer = io.BytesIO()
    img.save(out_buffer, format="JPEG", quality=90)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "logo.jpg"}
    await client.send_photo(message.chat_id, media, caption=f"🏷️ **Custom Logo for:** `{text}`")
    await status_msg.delete()


@astra_command(
    name="addbg",
    description="Save a custom background for the logo maker.",
    category="Creative Suite",
    usage="<reply to image>",
    owner_only=True,
)
async def addbg_handler(client: Client, message: Message):
    if not message.has_quoted_msg or getattr(message.quoted, 'type', None) != MessageType.IMAGE:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Reply to an image to save as background.")
    
    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Downloading background...")
    temp_path = f"/tmp/bg_{int(time.time())}.jpg"
    downloaded = await message.quoted.download()
    if not downloaded:
        downloaded = await message.quoted.download(temp_path)
    
    if downloaded:
        perm_path = os.path.join(LOGOS_DIR, f"bg_{int(time.time())}.jpg")
        os.rename(downloaded, perm_path)
        return await status_msg.edit(f"{UI.mono('[ OK ]')} Custom background added successfully!")
    return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Failed to download media.")


@astra_command(
    name="addfont",
    description="Save a custom font (.ttf) for the logo maker.",
    category="Creative Suite",
    usage="<reply to document>",
    owner_only=True,
)
async def addfont_handler(client: Client, message: Message):
    if not message.has_quoted_msg or getattr(message.quoted, 'type', None) != MessageType.DOCUMENT:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Reply to a font file (.ttf) to save.")
    
    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Downloading font...")
    temp_path = f"/tmp/font_{int(time.time())}.ttf"
    downloaded = await message.quoted.download()
    if not downloaded:
        downloaded = await message.quoted.download(temp_path)
    
    if downloaded:
        perm_path = os.path.join(LOGOS_DIR, f"font_{int(time.time())}.ttf")
        os.rename(downloaded, perm_path)
        return await status_msg.edit(f"{UI.mono('[ OK ]')} Custom font added successfully!")
    return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Failed to download font.")


@astra_command(
    name="listlogos",
    description="List all available custom backgrounds and fonts.",
    category="Creative Suite",
    usage="",
    is_public=True,
)
async def listlogos_handler(client: Client, message: Message):
    bgs = [f.rsplit('.', 1)[0] for f in os.listdir(LOGOS_DIR) if f.endswith((".jpg", ".jpeg", ".png"))]
    fonts = [f.rsplit('.', 1)[0] for f in os.listdir(LOGOS_DIR) if f.endswith(".ttf")]
    
    bg_list = ", ".join(bgs) if bgs else "None"
    font_list = ", ".join(fonts) if fonts else "None"
    
    out = (
        f"{UI.header('CREATIVE RESOURCES')}\n"
        f"**🖼️ Backgrounds:**\n`{bg_list}`\n\n"
        f"**🔤 Fonts:**\n`{font_list}`\n\n"
        f"{UI.mono('Use .clogo <bg> <font> <text> to create a custom logo.')}"
    )
    await edit_or_reply(message, out)


@astra_command(
    name="clogo",
    description="Create a logo with a specific background and font.",
    category="Creative Suite",
    usage="<bg_name> <font_name> <text>",
    is_public=True,
)
async def clogo_handler(client: Client, message: Message):
    args = extract_args(message)
    if len(args) < 3:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Usage: `.clogo <bg_name> <font_name> <text>`")

    bg_name = args[0]
    font_name = args[1]
    text = " ".join(args[2:])
    
    status_msg = await edit_or_reply(message, f"{UI.mono('[ BUSY ]')} Rendering custom logo...")
    
    # Resolve background
    bg_path = None
    for ext in [".jpg", ".jpeg", ".png"]:
        p = os.path.join(LOGOS_DIR, f"{bg_name}{ext}")
        if os.path.exists(p):
            bg_path = p
            break
            
    if not bg_path:
        return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Background `{bg_name}` not found. Check `.listlogos`.")
        
    # Resolve font
    font_path = os.path.join(LOGOS_DIR, f"{font_name}.ttf")
    if not os.path.exists(font_path):
        return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Font `{font_name}` not found. Check `.listlogos`.")
        
    # Render Logo
    try:
        img = Image.open(bg_path).convert("RGB")
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    except:
        return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Image `{bg_name}` is corrupted. Run `.addbg` to replace it or use a different one.")
        
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 130))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 180)
    except:
        font = ImageFont.load_default()
        
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((1024 - w) / 2, (1024 - h) / 2), text, font=font, fill=(255, 255, 255))
    
    out_buffer = io.BytesIO()
    img.save(out_buffer, format="JPEG", quality=90)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")
    
    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "clogo.jpg"}
    await client.send_photo(message.chat_id, media, caption=f"🏷️ **Custom Logo for:** `{text}`")
    await status_msg.delete()
