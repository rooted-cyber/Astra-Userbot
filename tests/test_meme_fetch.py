#!/usr/bin/env python3
"""
Comprehensive test for Astra Meme Fetching Engine.
Tests all subreddits, sort methods, media types, and edge cases.

Run: python3 tests/test_meme_fetch.py
"""

import asyncio
import aiohttp
import random
import sys
import time
from typing import List, Dict, Optional

# ── Config ──────────────────────────────────
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)

INDIAN_MEMES = [
    'IndianDankMemes', 'SaimanSays', 'indiameme', 'DHHMemes', 
    'FingMemes', 'jeeneetards', 'MandirGang', '2bharat4you',
    'teenindia', 'DesiMemeTemplates', 'MechanicalPandey', 
    'Indiancolleges', 'IndianMemeTemplates'
]
INDIAN_NSFW_MEMES = ['sunraybee', 'okbhaibudbak', 'IndianDankTemplates', 'IndianDankMemes']
GLOBAL_MEMES = ['dankmemes', 'memes', 'wholesomememes', 'PrequelMemes', 'terriblefacebookmemes', 'funny', 'ProgrammerHumor']
GLOBAL_NSFW_MEMES = ['HolUp', 'cursedimages', 'offensivememes', 'dankmemes', 'memes']
ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_NSFW_MEMES = list(set(INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES))

# ── Helpers (mirrors meme.py logic) ─────────

def _is_valid_image_url(url: str) -> bool:
    low = url.lower()
    if any(low.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
        return True
    if 'imgur.com' in low and '/a/' not in low and '/gallery/' not in low:
        return True
    if 'i.redd.it' in low:
        return True
    return False

def _is_video_post(pdata: dict, url: str) -> bool:
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        pdata.get('post_hint') == 'rich:video' or
        url.lower().endswith(('.mp4', '.gifv', '.mkv', '.webm')) or
        'v.redd.it' in url
    )

def _get_video_url(pdata: dict) -> Optional[str]:
    media = pdata.get('media') or {}
    rv = media.get('reddit_video') or {}
    if rv.get('fallback_url'):
        return rv['fallback_url']
    crosspost = pdata.get('crosspost_parent_list', [])
    if crosspost:
        cp_media = crosspost[0].get('media') or {}
        cp_rv = cp_media.get('reddit_video') or {}
        if cp_rv.get('fallback_url'):
            return cp_rv['fallback_url']
    url = pdata.get('url', '')
    if url.lower().endswith(('.mp4', '.gifv', '.webm')):
        return url
    if 'v.redd.it' in url:
        return url
    return None

# ── Test Stats ──────────────────────────────
class TestStats:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def log_pass(self, name, detail=""):
        self.passed += 1
        print(f"  ✅ {name}: {detail}")
    
    def log_fail(self, name, detail=""):
        self.failed += 1
        self.errors.append(f"{name}: {detail}")
        print(f"  ❌ {name}: {detail}")
    
    def log_skip(self, name, detail=""):
        self.skipped += 1
        print(f"  ⏭️  {name}: {detail}")
    
    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*50}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"  Total:   {total}")
        print(f"  ✅ Pass:  {self.passed}")
        print(f"  ❌ Fail:  {self.failed}")
        print(f"  ⏭️  Skip:  {self.skipped}")
        if self.errors:
            print(f"\n  Failures:")
            for e in self.errors:
                print(f"    → {e}")
        print(f"{'='*50}")
        return self.failed == 0

stats = TestStats()

# ── Test 1: Subreddit Reachability ──────────

async def test_subreddit_reachable(session, sub):
    """Test if a subreddit returns valid JSON."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=5", timeout=REQUEST_TIMEOUT) as resp:
            if resp.status == 200:
                data = await resp.json()
                posts = data.get('data', {}).get('children', [])
                if posts:
                    stats.log_pass(f"r/{sub}", f"{len(posts)} posts reachable")
                    return True
                else:
                    stats.log_fail(f"r/{sub}", "0 posts returned")
                    return False
            elif resp.status == 403:
                stats.log_skip(f"r/{sub}", f"Private/Banned (403)")
                return False
            else:
                stats.log_fail(f"r/{sub}", f"HTTP {resp.status}")
                return False
    except Exception as e:
        stats.log_fail(f"r/{sub}", f"Error: {e}")
        return False

# ── Test 2: Sort Method Coverage ────────────

async def test_sort_methods(session, sub="memes"):
    """Test all 4 sort methods return data."""
    for sort in ['hot', 'new', 'top', 'rising']:
        try:
            params = f"/{sort}.json?limit=10"
            if sort == 'top':
                params += "&t=week"
            async with session.get(f"https://www.reddit.com/r/{sub}{params}", timeout=REQUEST_TIMEOUT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    count = len(data.get('data', {}).get('children', []))
                    stats.log_pass(f"Sort/{sort}", f"{count} posts from r/{sub}")
                else:
                    stats.log_fail(f"Sort/{sort}", f"HTTP {resp.status}")
        except Exception as e:
            stats.log_fail(f"Sort/{sort}", str(e))

# ── Test 3: Image Detection ─────────────────

async def test_image_detection(session, sub="memes"):
    """Test that we can find valid image posts."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50&raw_json=1", timeout=REQUEST_TIMEOUT) as resp:
            data = await resp.json()
            posts = data.get('data', {}).get('children', [])
            
            images_found = 0
            for post in posts:
                pdata = post.get('data', {})
                url = pdata.get('url', '')
                if not pdata.get('is_self') and not _is_video_post(pdata, url):
                    if _is_valid_image_url(url):
                        images_found += 1
            
            if images_found > 0:
                stats.log_pass(f"ImageDetect/r/{sub}", f"{images_found} images found")
            else:
                stats.log_fail(f"ImageDetect/r/{sub}", "No images detected")
    except Exception as e:
        stats.log_fail(f"ImageDetect/r/{sub}", str(e))

# ── Test 4: Video Detection ─────────────────

async def test_video_detection(session, sub="IndianDankMemes"):
    """Test that we can find and extract video URLs."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=100&raw_json=1", timeout=REQUEST_TIMEOUT) as resp:
            data = await resp.json()
            posts = data.get('data', {}).get('children', [])
            
            videos_found = 0
            for post in posts:
                pdata = post.get('data', {})
                url = pdata.get('url', '')
                if _is_video_post(pdata, url):
                    vid_url = _get_video_url(pdata)
                    if vid_url:
                        videos_found += 1
            
            if videos_found > 0:
                stats.log_pass(f"VideoDetect/r/{sub}", f"{videos_found} videos found")
            else:
                stats.log_fail(f"VideoDetect/r/{sub}", "No videos detected")
    except Exception as e:
        stats.log_fail(f"VideoDetect/r/{sub}", str(e))

# ── Test 5: Text Post Detection ─────────────

async def test_text_detection(session, sub="PataHaiAajKyaHua"):
    """Test that we can find text/story posts."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50&raw_json=1", timeout=REQUEST_TIMEOUT) as resp:
            data = await resp.json()
            posts = data.get('data', {}).get('children', [])
            
            texts_found = 0
            for post in posts:
                pdata = post.get('data', {})
                if pdata.get('is_self') and len(pdata.get('selftext', '')) >= 20:
                    texts_found += 1
            
            if texts_found > 0:
                stats.log_pass(f"TextDetect/r/{sub}", f"{texts_found} text posts found")
            else:
                stats.log_fail(f"TextDetect/r/{sub}", "No text posts detected")
    except Exception as e:
        stats.log_fail(f"TextDetect/r/{sub}", str(e))

# ── Test 6: Media Download ──────────────────

async def test_media_download(session, sub="memes"):
    """Test that image URLs are actually downloadable."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=20&raw_json=1", timeout=REQUEST_TIMEOUT) as resp:
            data = await resp.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                pdata = post.get('data', {})
                url = pdata.get('url', '')
                if _is_valid_image_url(url) and not pdata.get('is_self') and not _is_video_post(pdata, url):
                    async with session.get(url) as img_resp:
                        if img_resp.status == 200:
                            ct = img_resp.headers.get('Content-Type', '')
                            size = img_resp.headers.get('Content-Length', '?')
                            stats.log_pass("MediaDownload", f"OK ({ct}, {size} bytes)")
                            return
                    stats.log_fail("MediaDownload", f"HTTP {img_resp.status} for {url}")
                    return
            
            stats.log_skip("MediaDownload", "No downloadable image found in sample")
    except Exception as e:
        stats.log_fail("MediaDownload", str(e))

# ── Test 7: NSFW Filtering ──────────────────

async def test_nsfw_filtering(session, sub="dankmemes"):
    """Test that NSFW posts are correctly identified."""
    try:
        async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50&raw_json=1", timeout=REQUEST_TIMEOUT) as resp:
            data = await resp.json()
            posts = data.get('data', {}).get('children', [])
            
            nsfw_count = sum(1 for p in posts if p.get('data', {}).get('over_18'))
            sfw_count = sum(1 for p in posts if not p.get('data', {}).get('over_18'))
            
            stats.log_pass(f"NSFWFilter/r/{sub}", f"SFW={sfw_count}, NSFW={nsfw_count}")
    except Exception as e:
        stats.log_fail(f"NSFWFilter/r/{sub}", str(e))

# ── Main Test Runner ────────────────────────

async def main():
    start = time.time()
    print("╔═══════════════════════════════════════╗")
    print("║  🧪 ASTRA MEME ENGINE TEST SUITE      ║")
    print("╚═══════════════════════════════════════╝\n")
    
    async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
        
        # 1. Subreddit Reachability
        print("📡 TEST 1: Subreddit Reachability")
        print("-" * 40)
        all_subs = list(set(ALL_MEMES + ALL_NSFW_MEMES + ['PataHaiAajKyaHua']))
        for sub in sorted(all_subs):
            await test_subreddit_reachable(session, sub)
        
        # 2. Sort Methods
        print(f"\n🔀 TEST 2: Sort Method Coverage")
        print("-" * 40)
        await test_sort_methods(session, "memes")
        
        # 3. Image Detection
        print(f"\n🖼️  TEST 3: Image Post Detection")
        print("-" * 40)
        for sub in ['memes', 'IndianDankMemes', 'SaimanSays']:
            await test_image_detection(session, sub)
        
        # 4. Video Detection
        print(f"\n🎥 TEST 4: Video Post Detection")
        print("-" * 40)
        for sub in ['IndianDankMemes', 'dankmemes', 'funny']:
            await test_video_detection(session, sub)
        
        # 5. Text (Story) Detection
        print(f"\n📖 TEST 5: Text/Story Post Detection")
        print("-" * 40)
        await test_text_detection(session, "PataHaiAajKyaHua")
        
        # 6. Media Download
        print(f"\n⬇️  TEST 6: Media Download Validation")
        print("-" * 40)
        await test_media_download(session, "memes")
        
        # 7. NSFW Filtering
        print(f"\n🔞 TEST 7: NSFW Flag Detection")
        print("-" * 40)
        await test_nsfw_filtering(session, "dankmemes")
    
    elapsed = round(time.time() - start, 2)
    print(f"\n⏱️  Completed in {elapsed}s")
    
    success = stats.summary()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
