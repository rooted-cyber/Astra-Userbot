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

            # 1. Attempt Native Framework Download
            try:
                data = await client.download_media(target)
                if data and len(data) > 100:
                    logger.info("Native download_media succeeded.")
                    return data
            except Exception as e:
                logger.debug(f"Native download_media failed: {e}")

            # 2. Injection Fallback: Extraction via Browser Bridge
            # We use client.bridge.call("eval", ...) to inject our custom blob extractor.
            # This uses WhatsApp's internal store to get the decrypted media blob.
            
            logger.info(f"Triggering bridge-level extraction for message: {target.id}")
            
            # The JS logic:
            # - Finds the message in the store using WhatsApp modules (mR)
            # - Leverages window.mR.findAndStore to locate internal controllers
            # - Ensures the media is downloaded locally in the browser
            # - Converts the resulting blob to base64
            
            js_script = f"""
            (async () => {{
                try {{
                    const msgId = "{target.id}";
                    if (!window.mR) throw new Error("WhatsApp Web Modules (mR) not found");
                    
                    const msg = window.mR.findAndStore("Msg")[0].get(msgId);
                    if (!msg) throw new Error("Message not found in internal store");
                    
                    // Trigger download if required (not downloading, not present)
                    const mediaDownload = window.mR.findAndStore("MediaDownload")[0];
                    if (msg.mediaData && msg.mediaData.mediaStage !== "REMOVING" && msg.mediaData.mediaStage !== "INIT") {{
                        if (mediaDownload && typeof mediaDownload.downloadMediaMessage === "function") {{
                            await mediaDownload.downloadMediaMessage(msg);
                        }}
                    }}
                    
                    // Attempt to get blob URL
                    const blobUrl = msg.mediaData?.mediaObject?.getBlobUrl();
                    if (!blobUrl) throw new Error("No blob URL available for this media");
                    
                    const blob = await window.mR.findAndStore("MediaBlob")[0].getBlob(blobUrl);
                    if (!blob) throw new Error("Blob retrieval failed from internal cache");
                    
                    return new Promise((resolve, reject) => {{
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = () => reject(new Error("FileReader failed"));
                        reader.readAsDataURL(blob);
                    }});
                }} catch (e) {{
                    return {{ error: e.message }};
                }}
            }})();
            """
            
            # Note: client.bridge.call("eval", script) is a common pattern in 
            # bridge-based frameworks for running arbitrary JS.
            b64_data = await client.bridge.call("eval", js_script)
            
            if isinstance(b64_data, dict) and "error" in b64_data:
                logger.error(f"Bridge extraction failed: {b64_data['error']}")
                return None
            
            if b64_data:
                return base64.b64decode(b64_data)
                
        except Exception as e:
            logger.error(f"Fatal error in Universal Bridge Downloader: {e}")
            
        return None

# Singleton-style access
bridge_downloader = AstraBridge()
