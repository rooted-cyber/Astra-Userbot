import asyncio
import base64
import logging
import os
from typing import Optional

from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.BridgeDownloader")


class AstraBridge:
    """High-reliability media downloader with multi-strategy fallbacks."""

    @staticmethod
    async def download_media(client: Client, message: Message) -> Optional[bytes]:
        """
        Downloads media from a message using multiple strategies.
        Accepts the actual media message directly — caller handles quoted resolution.
        """
        try:
            # Resolve target: if message quotes another, download from the quoted msg
            target = message.quoted if message.has_quoted_msg else message
            if not target or not target.is_media:
                logger.debug("Download skipped: not a media message.")
                return None

            mid = target.id
            logger.info(f"📥 Bridge Attempting Download: {mid}")

            # Strategy 1: Engine native media download (chunked/b64)
            for attempt in range(2):
                try:
                    data_b64 = await client.download_media(mid)
                    if data_b64:
                        logger.info(f"✅ Download OK (Native B64): {mid}")
                        return base64.b64decode(data_b64)

                    file_path = await client.media.download(message)
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            data = f.read()
                        os.remove(file_path)
                        logger.info(f"✅ Download OK (Native File): {mid}")
                        return data
                except Exception as e:
                    logger.debug(f"Native attempt {attempt + 1} failed: {e}")

                await asyncio.sleep(1)

            # Strategy 2: Direct JS DOM blob extraction
            logger.warning(f"⚠️ Native download failed for {mid}. Trying JS fallback...")

            # Use the short stanza part for DOM selector matching
            short_id = mid.split("_")[-1] if "_" in mid else mid

            js_fallback = f"""
            (async () => {{
                const msgId = "{mid}";
                const shortId = "{short_id}";

                // Try full ID first, then partial
                let el = document.querySelector(`div[data-id="${{msgId}}"] img, div[data-id="${{msgId}}"] video`);
                if (!el) {{
                    el = document.querySelector(`div[data-id*="${{shortId}}"] img, div[data-id*="${{shortId}}"] video`);
                }}

                if (el && el.src && el.src.startsWith('blob:')) {{
                    const res = await fetch(el.src);
                    const blob = await res.blob();
                    return await new Promise((resolve, reject) => {{
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    }});
                }}
                return null;
            }})()
            """

            try:
                res_b64 = await client.bridge.execute(js_fallback)
                if res_b64:
                    logger.info(f"🚀 JS Fallback SUCCESS for {mid}")
                    return base64.b64decode(res_b64)
            except Exception as e:
                logger.error(f"JS Fallback failed: {e}")

        except Exception as e:
            logger.error(f"Fatal error in BridgeDownloader: {e}")

        return None


bridge_downloader = AstraBridge()
