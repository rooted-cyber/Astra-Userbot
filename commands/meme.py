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
import json
from typing import List, Optional, Dict
from . import *
from utils.helpers import safe_edit, smart_reply, report_error
from utils.database import db

# Shared configuration for requests
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# --- Subreddit Lists ---
INDIAN_MEMES = [
    'IndianDankMemes', 'SaimanSays', 'indiameme', 'DHHMemes', 
    'FingMemes', 'jeeneetards', 'MandirGang', '2bharat4you',
    'teenindia', 'DesiMemeTemplates', 'MechanicalPandey', 
    'Indiancolleges', 'IndianMemeTemplates'
]

INDIAN_NSFW_MEMES = [
    'sunraybee', 'okbhaibudbak', 'IndianDankTemplates'
]

GLOBAL_MEMES = [
    'dankmemes', 'memes', 'wholesomememes', 'PrequelMemes', 
    'terriblefacebookmemes', 'funny', 'ProgrammerHumor'
]

GLOBAL_NSFW_MEMES = [
    'nsfw_memes', 'HolUp', 'dark_memes', 'cursedimages', 'offensivememes'
]

# Mixing for "Global" (includes Indian as requested)
ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_NSFW_MEMES = INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES

async def is_meme_seen(post_id: str) -> bool:
    """Checks if a meme has already been shown."""
    cursor = await db.sqlite_conn.execute("SELECT 1 FROM seen_memes WHERE post_id = ?", (post_id,))
    return await cursor.fetchone() is not None

async def mark_meme_seen(post_id: str, subreddit: str):
    """Marks a meme as seen in the database."""
    await db.sqlite_conn.execute(
        "INSERT INTO seen_memes (post_id, subreddit, fetched_at) VALUES (?, ?, ?)",
        (post_id, subreddit, int(time.time()))
    )
    await db.sqlite_conn.commit()

async def fetch_reddit_meme(subreddits: List[str], video_only: bool = False, nsfw: bool = False, allow_text: bool = False) -> Optional[Dict]:
    """Fetches a fresh meme from Reddit with duplicate prevention and high variety."""
    if not subreddits: return None
    random.shuffle(subreddits)
    
    # Range of sorting methods to get both latest and all-time great memes
    sort_methods = ['hot', 'top', 'new', 'rising']
    random.shuffle(sort_methods)
    
    async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
        for sub in subreddits:
            for sort in sort_methods:
                try:
                    # Append ?t=all for top to get old gems occasionally
                    url_suffix = f"/{sort}.json?limit=100" # Increased depth
                    if sort == 'top':
                        url_suffix += "&t=" + random.choice(['day', 'week', 'month', 'year', 'all'])
                    
                    async with session.get(f"https://www.reddit.com/r/{sub}{url_suffix}", timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        
                        data = await resp.json()
                        posts = data.get('data', {}).get('children', [])
                        if not posts: continue
                        
                        random.shuffle(posts) # High randomization
                        
                        for post in posts:
                            pdata = post.get('data', {})
                            if not pdata or pdata.get('stickied'): continue
                            
                            post_id = pdata.get('name') 
                            if await is_meme_seen(post_id):
                                continue
                            
                            # NSFW Logic
                            # If command is NOT nsfw-specific, we MUST skip over_18
                            # If command IS nsfw-specific, we can take both (as requested 'dmeme' etc)
                            if not nsfw and pdata.get('over_18'):
                                continue
                            
                            # Media Detection
                            url = pdata.get('url', '')
                            is_gallery = 'reddit.com/gallery/' in url
                            # Accurate video hint
                            is_video = (
                                pdata.get('is_video') or 
                                pdata.get('post_hint') == 'video' or 
                                url.lower().endswith(('.mp4', '.gifv', '.mkv')) or
                                'v.redd.it' in url
                            )
                            
                            # Handle text-only posts (for stories)
                            is_text = pdata.get('is_self', False)
                            
                            if is_text:
                                if not allow_text: continue
                                text_content = pdata.get('selftext')
                                if not text_content or len(text_content) < 20: continue
                                
                                return {
                                    "id": post_id,
                                    "title": pdata.get('title'),
                                    "subreddit": pdata.get('subreddit'),
                                    "text": text_content,
                                    "is_video": False,
                                    "is_nsfw": pdata.get('over_18'),
                                    "is_text": True
                                }

                            if video_only:
                                if not is_video: continue
                                if pdata.get('is_video') or 'v.redd.it' in url:
                                    url = pdata.get('media', {}).get('reddit_video', {}).get('fallback_url')
                                    if not url: # Fallback for some crossposts
                                        url = pdata.get('url')
                            else:
                                if is_video or is_gallery: continue
                                # Direct media check
                                if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                    # Try to fix imgur links
                                    if 'imgur.com' in url and not url.endswith(('.jpg', '.png', '.gif')):
                                        url += '.jpg'
                                    else:
                                        continue
                                    
                            if not url: continue
                            
                            return {
                                "id": post_id,
                                "url": url,
                                "title": pdata.get('title'),
                                "subreddit": pdata.get('subreddit'),
                                "is_video": is_video,
                                "is_nsfw": pdata.get('over_18'),
                                "is_text": False
                            }
                except Exception:
                    continue
    return None

async def send_meme_media(client, chat_id, meme_data, reply_to):
    """Downloads and sends the meme media."""
    if meme_data.get('is_text'):
        # For text stories, we just send a message
        caption = f"📖 *{meme_data['title']}*\n\n{meme_data['text']}\n\n📍 *Sub:* r/{meme_data['subreddit']}"
        if meme_data['is_nsfw']:
            caption = "🔞 " + caption
        
        # WhatsApp has a limit, trim if necessary
        if len(caption) > 4000:
            caption = caption[:4000] + "..."
            
        await client.send_message(chat_id, caption, reply_to=reply_to)
        return True

    async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
        async with session.get(meme_data['url']) as resp:
            if resp.status != 200:
                return False
            img_data = await resp.read()

    b64_data = base64.b64encode(img_data).decode('utf-8')
    mimetype = resp.headers.get('Content-Type', 'image/jpeg')
    
    # Correct extension for filename
    ext = mimetype.split('/')[-1] if '/' in mimetype else 'jpg'
    
    media = {
        "mimetype": mimetype,
        "data": b64_data,
        "filename": f"meme_{meme_data['subreddit']}.{ext}"
    }

    caption = f"🔥 *{meme_data['title']}*\n\n📍 *Sub:* r/{meme_data['subreddit']}"
    if meme_data['is_nsfw']:
        caption = "🔞 " + caption

    await client.send_media(
        chat_id,
        media,
        caption=caption,
        reply_to=reply_to
    )
    return True

# --- Handlers ---

@astra_command(
    name="imeme",
    description="Get a spicy Indian meme",
    category="Fun & Games",
    usage=".imeme"
)
async def imeme_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🇮🇳 *Fetching Indian meme...*")
    meme = await fetch_reddit_meme(INDIAN_MEMES, nsfw=False)
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Failed to download meme media.")
    else:
        await safe_edit(status_msg, "❌ No fresh Indian memes found right now.")

@astra_command(
    name="idmdmes",
    description="Get a NSFW/Edgy Indian meme",
    category="Fun & Games",
    usage=".idmdmes"
)
async def idmdmes_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🔞 *Fetching Edgy Indian meme...*")
    meme = await fetch_reddit_meme(INDIAN_NSFW_MEMES, nsfw=True)
    if not meme: # Fallback to general Indian memes but allow NSFW
        meme = await fetch_reddit_meme(INDIAN_MEMES, nsfw=True)
        
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Failed to download meme.")
    else:
        await safe_edit(status_msg, "❌ No dark Indian memes found.")

@astra_command(
    name="meme",
    description="Get a random global meme",
    category="Fun & Games",
    usage=".meme"
)
async def meme_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🌎 *Fetching global meme...*")
    meme = await fetch_reddit_meme(ALL_MEMES, nsfw=False)
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh memes found.")

@astra_command(
    name="dmeme",
    description="Get a NSFW/Dark global meme",
    category="Fun & Games",
    usage=".dmeme"
)
async def dmeme_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🔞 *Fetching dark global meme...*")
    meme = await fetch_reddit_meme(ALL_NSFW_MEMES, nsfw=True)
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, "❌ No dark memes found.")

@astra_command(
    name="vmemes",
    description="Get a random video meme",
    category="Fun & Games",
    usage=".vmemes"
)
async def vmemes_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🎥 *Fetching video meme...*")
    meme = await fetch_reddit_meme(ALL_MEMES, video_only=True, nsfw=False)
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Video download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh video memes found.")

@astra_command(
    name="vdmemes",
    description="Get a NSFW video meme (supports subreddit arg)",
    category="Fun & Games",
    usage=".vdmemes [subreddit]"
)
async def vdmemes_handler(client: Client, message: Message):
    args = extract_args(message)
    target_sub = args[0] if args else None
    
    status_msg = await smart_reply(message, f"🔞🎥 *Fetching dark video meme{' from r/' + target_sub if target_sub else ''}...*")
    
    subs = [target_sub] if target_sub else ALL_NSFW_MEMES
    meme = await fetch_reddit_meme(subs, video_only=True, nsfw=True)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Video download failed.")
    else:
        error_txt = f"❌ No fresh dark video memes found{' in r/' + target_sub if target_sub else ''}."
        await safe_edit(status_msg, error_txt)

@astra_command(
    name="idm",
    description="Get a meme from r/IndianDankMemes",
    category="Fun & Games",
    usage=".idm [-v]"
)
async def idm_handler(client: Client, message: Message):
    args = extract_args(message)
    video_only = "-v" in args
    
    status_msg = await smart_reply(message, f"🇮🇳 {'🎥 ' if video_only else ''}*Fetching IDM meme...*")
    meme = await fetch_reddit_meme(['IndianDankMemes'], video_only=video_only, nsfw=False)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, f"❌ No fresh {'video ' if video_only else ''}memes found in r/IndianDankMemes.")

@astra_command(
    name="phakh",
    description="Get a story from r/PataHaiAajKyaHua",
    aliases=["story"],
    category="Fun & Games",
    usage=".phakh"
)
async def phakh_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "📖 *Fetching a spicy story from r/PataHaiAajKyaHua...*")
    meme = await fetch_reddit_meme(['PataHaiAajKyaHua'], allow_text=True, nsfw=False)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Failed to fetch story content.")
    else:
        await safe_edit(status_msg, "❌ No fresh stories found in r/PataHaiAajKyaHua.")

@astra_command(
    name="ivdmeme",
    description="Get a spicy Indian NSFW video",
    category="Fun & Games",
    usage=".ivdmeme"
)
async def ivdmeme_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🔞🇮🇳🎥 *Fetching Indian dark video meme...*")
    meme = await fetch_reddit_meme(INDIAN_NSFW_MEMES, video_only=True, nsfw=True)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Video download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh Indian NSFW videos found.")

@astra_command(
    name="idmvd",
    description="Get a NSFW video from r/IndianDankMemes",
    category="Fun & Games",
    usage=".idmvd"
)
async def idmvd_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🔞🇮🇳🎥 *Fetching IDM dark video meme...*")
    meme = await fetch_reddit_meme(['IndianDankMemes'], video_only=True, nsfw=True)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh NSFW video memes found in r/IndianDankMemes.")

@astra_command(
    name="ivmeme",
    description="Get a spicy Indian safe video meme",
    category="Fun & Games",
    usage=".ivmeme"
)
async def ivmeme_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🇮🇳🎥 *Fetching Indian video meme...*")
    meme = await fetch_reddit_meme(INDIAN_MEMES, video_only=True, nsfw=False)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Video download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh Indian safe videos found.")

@astra_command(
    name="idmv",
    description="Get a safe video from r/IndianDankMemes",
    category="Fun & Games",
    usage=".idmv"
)
async def idmv_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🇮🇳🎥 *Fetching IDM video meme...*")
    meme = await fetch_reddit_meme(['IndianDankMemes'], video_only=True, nsfw=False)
    
    if meme:
        if await send_meme_media(client, message.chat_id, meme, message.id):
            await mark_meme_seen(meme['id'], meme['subreddit'])
            await status_msg.delete()
        else:
            await safe_edit(status_msg, "❌ Media download failed.")
    else:
        await safe_edit(status_msg, "❌ No fresh safe video memes found in r/IndianDankMemes.")
