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

# ── Config ──────────────────────────────────
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)
REDDIT_HEADERS = {
    'User-Agent': 'AstraUserbot/1.0 (by /u/AstraBot)',
    'Accept': 'application/json'
}

# ── Subreddit Lists ────────────────────────
INDIAN_MEMES = [
    'IndianDankMemes', 'SaimanSays', 'indiameme', 'DHHMemes', 
    'FingMemes', 'jeeneetards', 'MandirGang', '2bharat4you',
    'teenindia', 'DesiMemeTemplates', 'MechanicalPandey', 
    'Indiancolleges', 'IndianMemeTemplates'
]

INDIAN_NSFW_MEMES = [
    'sunraybee', 'okbhaibudbak', 'IndianDankTemplates',
    'IndianDankMemes'
]

GLOBAL_MEMES = [
    'dankmemes', 'memes', 'wholesomememes', 'PrequelMemes', 
    'terriblefacebookmemes', 'funny', 'ProgrammerHumor'
]

GLOBAL_VIDEO_MEMES = [
    'MemeVideos', 'VideoMemes', 'perfectlycutscreams', 'unexpected', 
    'maybemaybemaybe', 'nonononoyes', 'yesyesyesno'
]

GLOBAL_NSFW_MEMES = [
    'HolUp', 'cursedimages', 'ImFinnaGoToHell',
    'dankmemes', 'memes'
]

ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_VIDEO_MEMES = INDIAN_MEMES + GLOBAL_VIDEO_MEMES
ALL_NSFW_MEMES = list(set(INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES))

# ── Database Helpers ────────────────────────

async def _db_ok() -> bool:
    try: return db.sqlite_conn is not None
    except: return False

async def cleanup_old_seen(hours: int = 24):
    """Purge seen entries older than N hours so memes recycle."""
    try:
        if not await _db_ok(): return
        cutoff = int(time.time()) - (hours * 3600)
        await db.sqlite_conn.execute("DELETE FROM seen_memes WHERE fetched_at < ?", (cutoff,))
        await db.sqlite_conn.commit()
    except Exception: pass

async def is_meme_seen(post_id: str) -> bool:
    try:
        if not await _db_ok(): return False
        cur = await db.sqlite_conn.execute("SELECT 1 FROM seen_memes WHERE post_id = ?", (post_id,))
        return await cur.fetchone() is not None
    except: return False

async def mark_meme_seen(post_id: str, subreddit: str):
    try:
        if not await _db_ok(): return
        await db.sqlite_conn.execute(
            "INSERT OR IGNORE INTO seen_memes (post_id, subreddit, fetched_at) VALUES (?, ?, ?)",
            (post_id, subreddit, int(time.time()))
        )
        await db.sqlite_conn.commit()
    except Exception as e:
        logger.debug(f"mark_seen: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 1: MEME-API (Primary — fast, reliable)
# Uses meme-api.com which proxies Reddit server-side
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_video_post(pdata: dict, url: str) -> bool:
    """Enhanced video detection."""
    low_url = url.lower()
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        pdata.get('post_hint') == 'rich:video' or
        any(ext in low_url for ext in ['.mp4', '.gifv', '.mkv', '.webm', '.mov']) or
        'v.redd.it' in low_url or
        'youtube.com/shorts' in low_url or
        'youtube.com/watch' in low_url or
        'youtu.be' in low_url
    )

async def _fetch_via_meme_api(subreddits: List[str], nsfw: bool = False, video_only: bool = False) -> Optional[Dict]:
    """Fetch from meme-api.com — handles Reddit scraping server-side."""
    subs = list(subreddits)
    random.shuffle(subs)
    
    # Use a safer batch size (20 instead of 50) to avoid 400/403 errors
    count = 20 if video_only else 5
    
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            # Phase 1: Try specific subreddits
            for sub in subs[:10]:
                try:
                    url = f"https://meme-api.com/gimme/{sub}/{count}"
                    async with session.get(url) as resp:
                        if resp.status != 200: continue
                        data = await resp.json()
                        memes = data.get('memes', [])
                        if not memes and data.get('url'): memes = [data]
                        
                        random.shuffle(memes)
                        for meme in memes:
                            pid = meme.get('postLink', '')
                            if await is_meme_seen(pid): continue
                            if not nsfw and meme.get('nsfw'): continue
                            
                            m_url = meme.get('url', '')
                            if not m_url: continue
                            
                            is_vid = _is_video_post({}, m_url)
                            if video_only and not is_vid: continue
                            
                            return {
                                "id": pid, "url": m_url,
                                "title": meme.get('title', 'Meme'),
                                "subreddit": meme.get('subreddit', sub),
                                "is_video": is_vid, "is_nsfw": meme.get('nsfw', False),
                                "is_text": False
                            }
                except Exception: continue
            
            # Phase 2: Global Fallback for videos if subs failed
            if video_only:
                try:
                    url = f"https://meme-api.com/gimme/50"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            memes = data.get('memes', [])
                            random.shuffle(memes)
                            for meme in memes:
                                pid = meme.get('postLink', '')
                                if await is_meme_seen(pid): continue
                                if not nsfw and meme.get('nsfw'): continue
                                m_url = meme.get('url', '')
                                if _is_video_post({}, m_url):
                                    return {
                                        "id": pid, "url": m_url,
                                        "title": meme.get('title', 'Meme'),
                                        "subreddit": meme.get('subreddit', meme.get('subreddit', 'unknown')),
                                        "is_video": True, "is_nsfw": meme.get('nsfw', False),
                                        "is_text": False
                                    }
                except Exception: pass
                
    except Exception as e:
        logger.debug(f"meme-api session error: {e}")
    
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 2: DIRECT REDDIT (Fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_video_post(pdata: dict, url: str) -> bool:
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        'v.redd.it' in url or
        url.lower().endswith(('.mp4', '.gifv', '.webm'))
    )

def _get_video_url(pdata: dict) -> Optional[str]:
    for src in [pdata.get('media'), pdata.get('secure_media')]:
        if src and src.get('reddit_video', {}).get('fallback_url'):
            return src['reddit_video']['fallback_url']
    for cp in pdata.get('crosspost_parent_list', []):
        for src in [cp.get('media'), cp.get('secure_media')]:
            if src and src.get('reddit_video', {}).get('fallback_url'):
                return src['reddit_video']['fallback_url']
    url = pdata.get('url', '')
    if 'v.redd.it' in url or url.lower().endswith(('.mp4', '.gifv')):
        return url
    return None

async def _fetch_via_reddit(
    subreddits: List[str], video_only: bool = False, 
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Direct Reddit JSON fallback."""
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ['hot', 'new', 'top']
    random.shuffle(sorts)
    
    try:
        async with aiohttp.ClientSession(headers=REDDIT_HEADERS, timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:5]:
                for sort in sorts:
                    try:
                        params = f"/{sort}.json?limit=50&raw_json=1"
                        if sort == 'top':
                            params += "&t=" + random.choice(['day', 'week', 'month'])
                        
                        async with session.get(f"https://www.reddit.com/r/{sub}{params}") as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json()
                        
                        posts = data.get('data', {}).get('children', [])
                        if not posts: continue
                        random.shuffle(posts)
                        
                        for post in posts:
                            p = post.get('data', {})
                            if not p or p.get('stickied'): continue
                            
                            pid = p.get('name', '')
                            if not pid or await is_meme_seen(pid): continue
                            if not nsfw and p.get('over_18'): continue
                            
                            url = p.get('url', '')
                            is_vid = _is_video_post(p, url)
                            is_text = p.get('is_self', False)
                            is_gallery = p.get('is_gallery') or 'reddit.com/gallery/' in url
                            
                            # Text posts (stories)
                            if is_text:
                                if not allow_text: continue
                                text = p.get('selftext', '')
                                if len(text) < 20: continue
                                return {
                                    "id": pid, "title": p.get('title', ''),
                                    "subreddit": p.get('subreddit', sub),
                                    "text": text, "is_video": False,
                                    "is_nsfw": bool(p.get('over_18')), "is_text": True
                                }
                            
                            # Video posts
                            if video_only:
                                if not is_vid: continue
                                vid_url = _get_video_url(p)
                                if not vid_url: continue
                                return {
                                    "id": pid, "url": vid_url,
                                    "title": p.get('title', ''),
                                    "subreddit": p.get('subreddit', sub),
                                    "is_video": True, "is_nsfw": bool(p.get('over_18')),
                                    "is_text": False
                                }
                            
                            # Image posts
                            if is_vid or is_gallery or is_text: continue
                            low = url.lower()
                            if not any(low.endswith(e) for e in ['.jpg','.jpeg','.png','.gif','.webp']):
                                if 'i.redd.it' not in low and 'imgur.com' not in low:
                                    continue
                                if 'imgur.com' in url and '/a/' not in url and '/gallery/' not in url:
                                    url += '.jpg'
                            
                            return {
                                "id": pid, "url": url,
                                "title": p.get('title', ''),
                                "subreddit": p.get('subreddit', sub),
                                "is_video": False, "is_nsfw": bool(p.get('over_18')),
                                "is_text": False
                            }
                    except Exception as e:
                        logger.debug(f"reddit fallback [{sub}/{sort}]: {e}")
                        continue
    except Exception as e:
        logger.debug(f"reddit session error: {e}")
    
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIFIED FETCHER (tries sources in order)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_meme(
    subreddits: List[str], video_only: bool = False,
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Multi-source meme fetcher: meme-api → direct Reddit."""
    await cleanup_old_seen(24)
    
    # Source 1: meme-api.com (Primary for both Image and Video)
    if not allow_text:
        result = await _fetch_via_meme_api(subreddits, nsfw=nsfw, video_only=video_only)
        if result:
            return result
    
    # Source 2: Direct Reddit (Fallback)
    result = await _fetch_via_reddit(subreddits, video_only=video_only, nsfw=nsfw, allow_text=allow_text)
    if result:
        return result
    
    # Source 3: meme-api with broader subs as last resort
    if not allow_text:
        fallback_subs = ALL_VIDEO_MEMES if video_only else ALL_MEMES
        result = await _fetch_via_meme_api(fallback_subs, nsfw=nsfw, video_only=video_only)
        if result:
            return result
    
    logger.warning(f"All sources exhausted. video={video_only} nsfw={nsfw} text={allow_text}")
    return None

# ── Media Sender ────────────────────────────

async def send_meme_media(client, chat_id, meme_data, reply_to):
    """Downloads and sends the meme media to chat."""
    if meme_data.get('is_text'):
        caption = f"📖 *{meme_data['title']}*\n\n{meme_data['text']}\n\n📍 *Sub:* r/{meme_data['subreddit']}"
        if meme_data.get('is_nsfw'): caption = "🔞 " + caption
        if len(caption) > 4000: caption = caption[:3997] + "..."
        await client.send_message(chat_id, caption, reply_to=reply_to)
        return True

    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(meme_data['url']) as resp:
                if resp.status != 200:
                    logger.warning(f"Media download HTTP {resp.status}: {meme_data['url']}")
                    return False
                img_data = await resp.read()
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
    except Exception as e:
        logger.warning(f"Media download error: {e}")
        return False

    b64_data = base64.b64encode(img_data).decode('utf-8')
    ext_map = {
        'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif',
        'image/webp': 'webp', 'video/mp4': 'mp4'
    }
    ext = ext_map.get(content_type, 'jpg')
    
    media = {
        "mimetype": content_type,
        "data": b64_data,
        "filename": f"meme_{meme_data['subreddit']}.{ext}"
    }

    caption = f"🔥 *{meme_data['title']}*\n\n📍 *Sub:* r/{meme_data['subreddit']}"
    if meme_data.get('is_nsfw'): caption = "🔞 " + caption
    await client.send_media(chat_id, media, caption=caption, reply_to=reply_to)
    return True

# ── Generic Handler (DRY) ──────────────────

async def _meme_handler(client, message, subs, label, fallback_subs=None, **kwargs):
    """Generic meme command handler."""
    status_msg = await smart_reply(message, f"*{label}*")
    
    try:
        meme = await fetch_meme(subs, **kwargs)
        
        if not meme and fallback_subs:
            meme = await fetch_meme(fallback_subs, **kwargs)
        
        if meme:
            ok = await send_meme_media(client, message.chat_id, meme, message.id)
            if ok:
                await mark_meme_seen(meme['id'], meme['subreddit'])
                await status_msg.delete()
            else:
                await safe_edit(status_msg, f"❌ Media download failed.\n📎 URL: `{meme.get('url', '?')[:80]}`")
        else:
            subs_tried = ', '.join(subs[:3])
            mode = []
            if kwargs.get('video_only'): mode.append('video')
            if kwargs.get('nsfw'): mode.append('nsfw')
            if kwargs.get('allow_text'): mode.append('text')
            mode_str = '+'.join(mode) if mode else 'image'
            await safe_edit(status_msg, f"❌ No fresh content found.\n🔍 Subs: `{subs_tried}`\n📂 Mode: `{mode_str}`\n💡 Try again or use a different command.")
    except Exception as e:
        logger.error(f"_meme_handler error: {e}")
        await safe_edit(status_msg, f"❌ Meme Error: `{str(e)[:100]}`")

# ── Command Handlers ───────────────────────

@astra_command(name="imeme", description="Get a spicy Indian meme", category="Fun & Memes", usage=".imeme")
async def imeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳 Fetching Indian meme...")

@astra_command(name="idmdmes", description="Get a NSFW/Edgy Indian meme", category="Fun & Memes", usage=".idmdmes")
async def idmdmes_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞 Fetching edgy Indian meme...", fallback_subs=INDIAN_MEMES, nsfw=True)

@astra_command(name="meme", description="Get a random global meme", category="Fun & Memes", usage=".meme")
async def meme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_MEMES, "🌍 Fetching global meme...")

@astra_command(name="dmeme", description="Get a NSFW/Dark global meme", category="Fun & Memes", usage=".dmeme")
async def dmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_NSFW_MEMES, "🔞 Fetching dark meme...", fallback_subs=ALL_MEMES, nsfw=True)

@astra_command(name="vmemes", description="Get a random video meme", category="Fun & Memes", usage=".vmemes")
async def vmemes_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_VIDEO_MEMES, "🎥 Fetching video meme...", video_only=True)

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
    await _meme_handler(client, message, ['IndianDankMemes'], label, fallback_subs=ALL_VIDEO_MEMES, video_only=video_only)

@astra_command(name="phakh", description="Get a story from r/PataHaiAajKyaHua", aliases=["story"], category="Fun & Memes", usage=".phakh")
async def phakh_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['PataHaiAajKyaHua'], "📖 Fetching story...", allow_text=True)

@astra_command(name="ivdmeme", description="Get an Indian NSFW video", category="Fun & Memes", usage=".ivdmeme")
async def ivdmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞🇮🇳🎥 Fetching Indian dark video...", fallback_subs=ALL_VIDEO_MEMES, video_only=True, nsfw=True)

@astra_command(name="idmvd", description="Get a NSFW video from r/IndianDankMemes", category="Fun & Memes", usage=".idmvd")
async def idmvd_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🔞🇮🇳🎥 Fetching IDM dark video...", video_only=True, nsfw=True)

@astra_command(name="ivmeme", description="Get an Indian safe video meme", category="Fun & Memes", usage=".ivmeme")
async def ivmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳🎥 Fetching Indian video meme...", fallback_subs=ALL_VIDEO_MEMES, video_only=True)

@astra_command(name="idmv", description="Get a safe video from r/IndianDankMemes", category="Fun & Memes", usage=".idmv")
async def idmv_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🇮🇳🎥 Fetching IDM video...", fallback_subs=ALL_VIDEO_MEMES, video_only=True)
