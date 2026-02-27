# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import base64
import logging
import asyncio
from typing import Optional
from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.BridgeDownloader")

class AstraBridge:
    """
    Universal High-Reliability Media Downloader.
    Bypasses framework-level decryption issues by injecting JS into the browser.
    """
    
    @staticmethod
    async def download_media(client: Client, message: Message) -> Optional[bytes]:
        """
        Downloads media from a message with a robust circular fallback logic.
        """
        try:
            target = message.quoted if message.has_quoted_msg else message
            if not target.is_media:
                return None

            # 1. Attempt Native Framework Download with slight delay/retry
            # Passing target.id (string) is the correct 'direct' way.
            for attempt in range(3):
                try:
                    # Use target.id to ensure framework-level string expectations are met
                    data_b64 = await client.download_media(target.id)
                    if data_b64:
                        return base64.b64decode(data_b64)
                except Exception as e:
                    logger.debug(f"Direct download attempt {attempt+1} failed: {e}")
                
                # Optional: Try saving to file if b64 retrieval fails
                try:
                    file_path = await client.media.download(target)
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            data = f.read()
                        os.remove(file_path) # Cleanup
                        return data
                except:
                    pass

                await asyncio.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Fatal error in Direct Downloader: {e}")
            
        return None
            
        return None

# Singleton-style access
bridge_downloader = AstraBridge()
