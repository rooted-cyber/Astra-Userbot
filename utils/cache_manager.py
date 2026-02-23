import os
import hashlib
import time
import json
import logging
import asyncio

logger = logging.getLogger("Astra.CacheManager")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "media_cache")
CACHE_META_FILE = os.path.join(CACHE_DIR, "cache_meta.json")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

class MediaCacheManager:
    """Manages temporary caching of downloaded media files to speed up duplicate requests."""
    
    def __init__(self):
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        if os.path.exists(CACHE_META_FILE):
            try:
                with open(CACHE_META_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
        return {}

    def _auto_cleanup(self):
        """Deletes cache entries older than 2 hours if CACHE_AUTO_DELETE is enabled."""
        from utils.state import state
        # Default True, user can disable with `.setcfg CACHE_AUTO_DELETE off`
        if str(state.get_config("CACHE_AUTO_DELETE")).lower() in ["false", "off", "0"]:
            return

        now = time.time()
        two_hours = 2 * 60 * 60
        to_delete = []

        for key, entry in self.metadata.items():
            timestamp = entry.get('timestamp', 0)
            if now - timestamp > two_hours:
                to_delete.append((key, entry.get('file_path')))

        if to_delete:
            for key, path in to_delete:
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                    del self.metadata[key]
                except Exception as e:
                    logger.debug(f"Failed to auto-delete {path}: {e}")
            self._save_metadata()

    def _save_metadata(self):
        try:
            with open(CACHE_META_FILE, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def generate_cache_key(self, url: str, mode: str) -> str:
        """Generates a unique MD5 hash based on the URL and format mode."""
        raw = f"{url}_{mode}".encode('utf-8')
        return hashlib.md5(raw).hexdigest()

    async def get_cached_file(self, url: str, mode: str):
        """Returns (file_path, metadata) if a valid cache exists, else (None, None)."""
        from utils.state import state
        if str(state.get_config("ENABLE_MEDIA_CACHE")).lower() in ["false", "off", "0"]:
            return None, None

        self._auto_cleanup()
        
        key = self.generate_cache_key(url, mode)
        
        if key in self.metadata:
            entry = self.metadata[key]
            file_path = entry.get('file_path')
            
            if file_path and os.path.exists(file_path):
                # Update last accessed time for potential LRU eviction later
                entry['last_accessed'] = time.time()
                self._save_metadata()
                return file_path, entry.get('media_meta', {})
            else:
                # File deleted manually or lost, clean up metadata
                del self.metadata[key]
                self._save_metadata()
                
        return None, None

    async def save_to_cache(self, url: str, mode: str, original_file_path: str, media_meta: dict) -> str:
        """Copies the downloaded file to the cache directory and stores metadata."""
        from utils.state import state
        if str(state.get_config("ENABLE_MEDIA_CACHE")).lower() in ["false", "off", "0"]:
            return original_file_path

        try:
            key = self.generate_cache_key(url, mode)
            ext = os.path.splitext(original_file_path)[1]
            cached_file_path = os.path.join(CACHE_DIR, f"{key}{ext}")
            
            # Copy file (using asyncio to avoid blocking, though shutil for small files is fast)
            import shutil
            await asyncio.to_thread(shutil.copy2, original_file_path, cached_file_path)
            
            self.metadata[key] = {
                'file_path': cached_file_path,
                'media_meta': media_meta,
                'timestamp': time.time(),
                'last_accessed': time.time()
            }
            self._save_metadata()
            return cached_file_path
        except Exception as e:
            logger.error(f"Failed to save file to cache: {e}")
            return original_file_path # Fallback to original if caching fails

    def clear_cache(self) -> dict:
        """Deletes all files in the cache directory and resets metadata."""
        count = 0
        size_freed = 0
        try:
            for filename in os.listdir(CACHE_DIR):
                filepath = os.path.join(CACHE_DIR, filename)
                if os.path.isfile(filepath):
                    size_freed += os.path.getsize(filepath)
                    os.remove(filepath)
                    count += 1
            
            self.metadata = {}
            self._save_metadata()
            
            # Convert to MB
            size_mb = size_freed / (1024 * 1024)
            return {"success": True, "files_deleted": count, "freed_mb": round(size_mb, 2)}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"success": False, "error": str(e)}

# Singleton instance
cache = MediaCacheManager()
