# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import random
import aiohttp
import base64
import time
import logging
from typing import List, Optional, Dict
from . import *
from utils.helpers import safe_edit, smart_reply, report_error
from utils.database import db

logger = logging.getLogger("Astra.Memes")

# ── Request Config ──────────────────────────
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

# ── Subreddit Lists ────────────────────────
INDIAN_MEMES = [
    'IndianDankMemes', 'SaimanSays', 'indiameme', 'DHHMemes', 
    'FingMemes', 'jeeneetards', 'MandirGang', '2bharat4you',
    'teenindia', 'DesiMemeTemplates', 'MechanicalPandey', 
    'Indiancolleges', 'IndianMemeTemplates'
]

INDIAN_NSFW_MEMES = [
    'sunraybee', 'okbhaibudbak', 'IndianDankTemplates',
    'IndianDankMemes'  # IDM also has nsfw content
]

GLOBAL_MEMES = [
    'dankmemes', 'memes', 'wholesomememes', 'PrequelMemes', 
    'terriblefacebookmemes', 'funny', 'ProgrammerHumor'
]

GLOBAL_NSFW_MEMES = [
    'HolUp', 'cursedimages', 'ImFinnaGoToHell',
    'dankmemes', 'memes'  # These also have NSFW tagged posts
]

# Combined lists
ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_NSFW_MEMES = list(set(INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES))

# ── Database Helpers ────────────────────────

async def is_meme_seen(post_id: str) -> bool:
    """Checks if a meme has already been shown."""
    try:
        cursor = await db.sqlite_conn.execute("SELECT 1 FROM seen_memes WHERE post_id = ?", (post_id,))
        return await cursor.fetchone() is not None
    except Exception:
        return False

async def mark_meme_seen(post_id: str, subreddit: str):
    """Marks a meme as seen in the database."""
    try:
        await db.sqlite_conn.execute(
            "INSERT OR IGNORE INTO seen_memes (post_id, subreddit, fetched_at) VALUES (?, ?, ?)",
            (post_id, subreddit, int(time.time()))
        )
        await db.sqlite_conn.commit()
    except Exception as e:
        logger.debug(f"mark_meme_seen error: {e}")

# ── Core Fetching Engine ────────────────────

def _is_valid_image_url(url: str) -> bool:
    """Check if a URL points to a direct image."""
    low = url.lower()
    if any(low.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return True
    # Imgur fix: bare imgur links without extension
    if 'imgur.com' in low and '/a/' not in low and '/gallery/' not in low:
        return True
    # i.redd.it is always a direct image
    if 'i.redd.it' in low:
        return True
    return False

def _fix_url(url: str) -> str:
    """Fix common URL issues."""
    # Imgur without extension
    if 'imgur.com' in url and not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        if '/a/' not in url and '/gallery/' not in url:
            return url + '.jpg'
    return url

def _is_video_post(pdata: dict, url: str) -> bool:
    """Accurate video detection."""
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        pdata.get('post_hint') == 'rich:video' or
        url.lower().endswith(('.mp4', '.gifv', '.mkv', '.webm')) or
        'v.redd.it' in url
    )

def _get_video_url(pdata: dict) -> Optional[str]:
    """Extract the best video URL from a reddit post."""
    # Reddit native video
    media = pdata.get('media') or {}
    rv = media.get('reddit_video') or {}
    if rv.get('fallback_url'):
        return rv['fallback_url']
    
    # Crosspost source
    crosspost = pdata.get('crosspost_parent_list', [])
    if crosspost:
        cp_media = crosspost[0].get('media') or {}
        cp_rv = cp_media.get('reddit_video') or {}
        if cp_rv.get('fallback_url'):
            return cp_rv['fallback_url']
    
    # Direct URL fallback
    url = pdata.get('url', '')
    if url.lower().endswith(('.mp4', '.gifv', '.webm')):
        return url
    if 'v.redd.it' in url:
        return url
    
    return None

async def fetch_reddit_meme(
    subreddits: List[str], 
    video_only: bool = False, 
    nsfw: bool = False, 
    allow_text: bool = False
) -> Optional[Dict]:
    """
    Fetches a fresh meme from Reddit with duplicate prevention and high variety.
    Scans multiple sort methods (hot, new, top, rising) across multiple subreddits.
    """
    if not subreddits:
        return None
    
    subs = list(subreddits)
    random.shuffle(subs)
    
    sort_methods = ['hot', 'new', 'top', 'rising']
    random.shuffle(sort_methods)
    
    async with aiohttp.ClientSession(headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT) as session:
        for sub in subs:
            for sort in sort_methods:
                try:
                    params = f"/{sort}.json?limit=100&raw_json=1"
                    if sort == 'top':
                        params += "&t=" + random.choice(['day', 'week', 'month', 'year', 'all'])
                    
                    url = f"https://www.reddit.com/r/{sub}{params}"
                    
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        
                        try:
                            data = await resp.json()
                        except Exception:
                            continue
                        
                        posts = data.get('data', {}).get('children', [])
                        if not posts:
                            continue
                        
                        random.shuffle(posts)
                        
                        for post in posts:
                            pdata = post.get('data', {})
                            if not pdata or pdata.get('stickied'):
                                continue
                            
                            post_id = pdata.get('name', '')
                            if not post_id:
                                continue
                            if await is_meme_seen(post_id):
                                continue
                            
                            # NSFW filter
                            if not nsfw and pdata.get('over_18'):
                                continue
                            
                            post_url = pdata.get('url', '')
                            is_gallery = 'reddit.com/gallery/' in post_url or pdata.get('is_gallery')
                            is_video = _is_video_post(pdata, post_url)
                            is_text = pdata.get('is_self', False)
                            
                            # ── TEXT POSTS (stories) ──
                            if is_text:
                                if not allow_text:
                                    continue
                                text_content = pdata.get('selftext', '')
                                if len(text_content) < 20:
                                    continue
                                return {
                                    "id": post_id,
                                    "title": pdata.get('title', ''),
                                    "subreddit": pdata.get('subreddit', sub),
                                    "text": text_content,
                                    "is_video": False,
                                    "is_nsfw": bool(pdata.get('over_18')),
                                    "is_text": True
                                }
                            
                            # ── VIDEO POSTS ──
                            if video_only:
                                if not is_video:
                                    continue
                                vid_url = _get_video_url(pdata)
                                if not vid_url:
                                    continue
                                return {
                                    "id": post_id,
                                    "url": vid_url,
                                    "title": pdata.get('title', ''),
                                    "subreddit": pdata.get('subreddit', sub),
                                    "is_video": True,
                                    "is_nsfw": bool(pdata.get('over_18')),
                                    "is_text": False
                                }
                            
                            # ── IMAGE POSTS ──
                            if is_video or is_gallery or is_text:
                                continue
                            
                            fixed_url = _fix_url(post_url)
                            if not _is_valid_image_url(fixed_url):
                                continue
                            
                            return {
                                "id": post_id,
                                "url": fixed_url,
                                "title": pdata.get('title', ''),
                                "subreddit": pdata.get('subreddit', sub),
                                "is_video": False,
                                "is_nsfw": bool(pdata.get('over_18')),
                                "is_text": False
                            }
                            
                except Exception as e:
                    logger.debug(f"fetch_reddit_meme error [{sub}/{sort}]: {e}")
                    continue
    
    return None

# ── Media Sender ────────────────────────────

async def send_meme_media(client, chat_id, meme_data, reply_to):
    """Downloads and sends the meme media to chat."""
    # Text-only stories
    if meme_data.get('is_text'):
        caption = f"📖 *{meme_data['title']}*\n\n{meme_data['text']}\n\n📍 *Sub:* r/{meme_data['subreddit']}"
        if meme_data.get('is_nsfw'):
            caption = "🔞 " + caption
        if len(caption) > 4000:
            caption = caption[:3997] + "..."
        await client.send_message(chat_id, caption, reply_to=reply_to)
        return True

    # Download media
    try:
        async with aiohttp.ClientSession(headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT) as session:
            async with session.get(meme_data['url']) as resp:
                if resp.status != 200:
                    return False
                img_data = await resp.read()
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
    except Exception as e:
        logger.debug(f"Media download error: {e}")
        return False

    b64_data = base64.b64encode(img_data).decode('utf-8')
    
    # Determine ext from content type
    ext_map = {
        'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif',
        'image/webp': 'webp', 'video/mp4': 'mp4', 'video/webm': 'webm'
    }
    ext = ext_map.get(content_type, content_type.split('/')[-1] if '/' in content_type else 'jpg')
    
    media = {
        "mimetype": content_type,
        "data": b64_data,
        "filename": f"meme_{meme_data['subreddit']}.{ext}"
    }

    caption = f"🔥 *{meme_data['title']}*\n\n📍 *Sub:* r/{meme_data['subreddit']}"
    if meme_data.get('is_nsfw'):
        caption = "🔞 " + caption

    await client.send_media(chat_id, media, caption=caption, reply_to=reply_to)
    return True

# ── Generic handler helper (DRY) ───────────

async def _meme_handler(client, message, subs, label, fallback_subs=None, **kwargs):
    """Generic meme handler to reduce code duplication."""
    status_msg = await smart_reply(message, f"*{label}*")
    
    meme = await fetch_reddit_meme(subs, **kwargs)
    
    # Fallback if primary list returned nothing
    if not meme and fallback_subs:
        meme = await fetch_reddit_meme(fallback_subs, **kwargs)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh content found. Try again!")

# ── Command Handlers ───────────────────────

@astra_command(name="imeme", description="Get a spicy Indian meme", category="Fun & Memes", usage=".imeme")
async def imeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳 Fetching Indian meme...")

@astra_command(name="idmdmes", description="Get a NSFW/Edgy Indian meme", category="Fun & Memes", usage=".idmdmes")
async def idmdmes_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞 Fetching edgy Indian meme...", fallback_subs=INDIAN_MEMES, nsfw=True)

@astra_command(name="meme", description="Get a random global meme", category="Fun & Memes", usage=".meme")
async def meme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_MEMES, "🌎 Fetching global meme...")

@astra_command(name="dmeme", description="Get a NSFW/Dark global meme", category="Fun & Memes", usage=".dmeme")
async def dmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_NSFW_MEMES, "🔞 Fetching dark meme...", fallback_subs=ALL_MEMES, nsfw=True)

@astra_command(name="vmemes", description="Get a random video meme", category="Fun & Memes", usage=".vmemes")
async def vmemes_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_MEMES, "🎥 Fetching video meme...", video_only=True)

@astra_command(name="vdmemes", description="Get a NSFW video meme", category="Fun & Memes", usage=".vdmemes [subreddit]")
async def vdmemes_handler(client: Client, message: Message):
    args = extract_args(message)
    target_sub = args[0] if args else None
    subs = [target_sub] if target_sub else ALL_NSFW_MEMES
    label = f"🔞🎥 Fetching dark video{' from r/' + target_sub if target_sub else ''}..."
    await _meme_handler(client, message, subs, label, fallback_subs=ALL_MEMES, video_only=True, nsfw=True)

@astra_command(name="idm", description="Get a meme from r/IndianDankMemes", category="Fun & Memes", usage=".idm [-v]")
async def idm_handler(client: Client, message: Message):
    args = extract_args(message)
    video_only = "-v" in args
    label = f"🇮🇳 {'🎥 ' if video_only else ''}Fetching IDM meme..."
    await _meme_handler(client, message, ['IndianDankMemes'], label, video_only=video_only)

@astra_command(name="phakh", description="Get a story from r/PataHaiAajKyaHua", aliases=["story"], category="Fun & Memes", usage=".phakh")
async def phakh_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['PataHaiAajKyaHua'], "📖 Fetching story...", allow_text=True)

@astra_command(name="ivdmeme", description="Get an Indian NSFW video", category="Fun & Memes", usage=".ivdmeme")
async def ivdmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞🇮🇳🎥 Fetching Indian dark video...", fallback_subs=INDIAN_MEMES, video_only=True, nsfw=True)

@astra_command(name="idmvd", description="Get a NSFW video from r/IndianDankMemes", category="Fun & Memes", usage=".idmvd")
async def idmvd_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🔞🇮🇳🎥 Fetching IDM dark video...", video_only=True, nsfw=True)

@astra_command(name="ivmeme", description="Get an Indian safe video meme", category="Fun & Memes", usage=".ivmeme")
async def ivmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳🎥 Fetching Indian video meme...", video_only=True)

@astra_command(name="idmv", description="Get a safe video from r/IndianDankMemes", category="Fun & Memes", usage=".idmv")
async def idmv_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🇮🇳🎥 Fetching IDM video...", video_only=True)
