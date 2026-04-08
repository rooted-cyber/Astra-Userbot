import asyncio
import base64
import logging
import os
from typing import Optional

from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.BridgeDownloader")

# Self-contained JS that resolves a message by short/full ID and downloads its media.
# This bypasses the engine's retrieveMedia entirely for maximum reliability.
INLINE_DOWNLOAD_JS = """
(async (msgRef) => {
    const Store = window.Astra.initializeEngine();
    const repo = Store.Msg || Store.MessageRepo || Store.MsgRepo;
    let msg = null;

    const toSerializedId = (ref) => {
        if (!ref) return null;
        if (typeof ref === 'string') return ref;
        if (typeof ref === 'object') {
            if (typeof ref._serialized === 'string') return ref._serialized;
            if (typeof ref.serialized === 'string') return ref.serialized;
            if (typeof ref.id === 'string') return ref.id;
            if (ref.id && typeof ref.id._serialized === 'string') return ref.id._serialized;
            if (ref.id && typeof ref.id.id === 'string' && ref.id.remote) {
                return `${ref.id.fromMe ? 'true' : 'false'}_${ref.id.remote}_${ref.id.id}`;
            }
        }
        return String(ref);
    };

    const msgId = toSerializedId(msgRef);
    if (!msgId) return { error: 'invalid_msg_id' };

    // --- Resolve msg from ID (supports both full serialized and short stanza IDs) ---

    // 1. Direct repo lookup
    try { msg = repo.get(msgId); } catch(e) {}

    // 2. MessageIdentity lookup
    if (!msg && Store.MessageIdentity && Store.MessageIdentity.fromString) {
        try { msg = repo.get(Store.MessageIdentity.fromString(msgId)); } catch(e) {}
    }

    // 3. getMessagesById API
    if (!msg) {
        try {
            const getById = repo.getMessagesById || Store.Msg?.getMessagesById;
            const r = getById ? await getById.call(repo, [msgId]) : null;
            msg = r && r.messages && r.messages[0];
        } catch(e) {}
    }

    // 4. Scan top-level repo by stanza ID (critical for quoted msg short IDs)
    if (!msg) {
        const shortId = msgId.includes('_') ? msgId.split('_').pop() : msgId;
        const models = repo.getModelsArray ? repo.getModelsArray() : (repo.models || []);
        msg = models.find(m => m.id && (m.id.id === shortId || m.id._serialized === msgId));
    }

    // 5. Per-chat message scan
    if (!msg && Store.Chat) {
        const shortId = msgId.includes('_') ? msgId.split('_').pop() : msgId;
        const chats = Store.Chat.getModelsArray ? Store.Chat.getModelsArray() : (Store.Chat.models || []);
        for (const chat of chats) {
            if (msg) break;
            if (!chat.msgs) continue;
            const msgs = chat.msgs.getModelsArray ? chat.msgs.getModelsArray() : (chat.msgs.models || []);
            msg = msgs.find(m => m.id && (m.id.id === shortId || m.id._serialized === msgId));
        }
    }

    if (!msg) return { error: 'msg_not_found' };

    // If resolved message is an album/summary/non-media node, try to pick a sibling media node.
    if (!(msg.directPath && msg.mediaKey)) {
        const models = repo.getModelsArray ? repo.getModelsArray() : (repo.models || []);
        const grouped = msg.groupedId || msg.grouped_id || msg.albumId || null;

        if (grouped) {
            const sibling = models.find(m => {
                const mg = m.groupedId || m.grouped_id || m.albumId || null;
                return mg === grouped && m.directPath && m.mediaKey;
            });
            if (sibling) msg = sibling;
        }

        if (!(msg.directPath && msg.mediaKey)) {
            const baseTs = msg.t || 0;
            const baseRemote = msg.id && msg.id.remote;
            const baseAuthor = msg.author || (msg.id && msg.id.participant) || null;
            const candidates = models
                .filter(m => m.directPath && m.mediaKey)
                .filter(m => !baseRemote || (m.id && m.id.remote === baseRemote))
                .filter(m => !baseAuthor || m.author === baseAuthor || (m.id && m.id.participant === baseAuthor))
                .filter(m => !baseTs || Math.abs((m.t || 0) - baseTs) <= 180)
                .sort((a, b) => Math.abs((a.t || 0) - baseTs) - Math.abs((b.t || 0) - baseTs));

            if (candidates.length) msg = candidates[0];
        }
    }

    // --- Download the media ---
    let buffer = null;

    // Strategy A: DownloadManager (encrypted download + decrypt)
    if (!buffer && msg.directPath && msg.mediaKey) {
        try {
            const dm = Store.DownloadManager;
            if (dm && dm.downloadAndMaybeDecrypt) {
                if (msg.mediaData && msg.mediaData.mediaStage !== 'RESOLVED') {
                    await msg.downloadMedia({ downloadEvenIfExpensive: true, rmrReason: 1 });
                }
                const qpl = { addAnnotations() { return this; }, addPoint() { return this; } };
                buffer = await dm.downloadAndMaybeDecrypt({
                    directPath: msg.directPath,
                    encFilehash: msg.encFilehash,
                    filehash: msg.filehash,
                    mediaKey: msg.mediaKey,
                    mediaKeyTimestamp: msg.mediaKeyTimestamp || msg.t,
                    type: msg.type,
                    signal: (new AbortController()).signal,
                    downloadQpl: qpl
                });
            }
        } catch(e) { console.warn('[BD] DownloadManager failed:', e); }
    }

    // Strategy B: msg.downloadMedia() then read blob
    if (!buffer && msg.downloadMedia) {
        try {
            await msg.downloadMedia({ downloadEvenIfExpensive: true, rmrReason: 1 });
            if (msg.mediaData && msg.mediaData.mediaBlob) {
                const blob = msg.mediaData.mediaBlob.forResume
                    ? msg.mediaData.mediaBlob.forResume() : msg.mediaData.mediaBlob;
                if (blob && typeof blob.arrayBuffer === 'function') {
                    buffer = new Uint8Array(await blob.arrayBuffer());
                }
            }
        } catch(e) { console.warn('[BD] downloadMedia blob failed:', e); }
    }

    // Strategy C: DOM blob scraping
    if (!buffer) {
        const fullId = msg.id && msg.id._serialized ? msg.id._serialized : msgId;
        const shortId = fullId.includes('_') ? fullId.split('_').pop() : fullId;
        try {
            if (Store.Cmd && Store.Cmd.scrollToMessage) {
                try { Store.Cmd.scrollToMessage(msg); await new Promise(r => setTimeout(r, 600)); } catch(e) {}
            }
            let el = document.querySelector(`div[data-id="${fullId}"] img, div[data-id="${fullId}"] video`);
            if (!el) el = document.querySelector(`div[data-id*="${shortId}"] img, div[data-id*="${shortId}"] video`);
            if (el && el.src && el.src.startsWith('blob:')) {
                const res = await fetch(el.src);
                const blob = await res.blob();
                buffer = new Uint8Array(await blob.arrayBuffer());
            }
        } catch(e) { console.warn('[BD] DOM scraping failed:', e); }
    }

    if (!buffer) return { error: 'download_failed' };

    // Convert to base64 using FileReader (fast, no char-by-char loop)
    const b = new Blob([buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer]);
    const b64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(b);
    });

    return {
        data: b64,
        mimetype: msg.mimetype || 'application/octet-stream',
        size: buffer.byteLength,
        resolvedId: msg.id && (msg.id._serialized || msg.id.id) ? (msg.id._serialized || msg.id.id) : msgId
    };
})
"""


class AstraBridge:
    """High-reliability media downloader — self-contained JS, no engine dependency."""

    @staticmethod
    async def download_media(client: Client, message: Message) -> Optional[bytes]:
        """
        Downloads media from a message using self-contained inline JS.
        Handles quoted message resolution automatically.
        """
        try:
            target = message.quoted if message.has_quoted_msg else message

            def _id_to_serialized(obj) -> Optional[str]:
                if obj is None:
                    return None
                if isinstance(obj, str):
                    return obj
                serialized = getattr(obj, "serialized", None)
                if isinstance(serialized, str):
                    return serialized
                serialized = getattr(obj, "_serialized", None)
                if isinstance(serialized, str):
                    return serialized
                rid = getattr(obj, "id", None)
                if isinstance(rid, str):
                    return rid
                if rid is not None:
                    nested = getattr(rid, "serialized", None) or getattr(rid, "_serialized", None)
                    if isinstance(nested, str):
                        return nested
                    if isinstance(rid, dict):
                        if isinstance(rid.get("_serialized"), str):
                            return rid["_serialized"]
                        if isinstance(rid.get("id"), str):
                            remote = rid.get("remote")
                            from_me = "true" if rid.get("fromMe") else "false"
                            return f"{from_me}_{remote}_{rid['id']}" if remote else rid["id"]
                return str(obj)

            mid = None
            if target is not None:
                mid = _id_to_serialized(getattr(target, "id", target))

            if not mid:
                mid = _id_to_serialized(
                    getattr(message, "quoted_message_id", None) or getattr(message, "quotedMessageId", None)
                )

            if not mid:
                mid = _id_to_serialized(getattr(message, "id", None))

            if not mid:
                logger.debug("Download skipped: no resolvable message id.")
                return None

            logger.info(f"📥 Bridge Attempting Download: {mid}")

            # Execute our self-contained JS directly on the browser page
            page = client.browser.page
            if not page:
                logger.error("No browser page available.")
                return None

            result = await page.evaluate(INLINE_DOWNLOAD_JS, mid)

            if result and isinstance(result, dict):
                if "error" in result:
                    logger.warning(f"⚠️ Inline JS download result: {result['error']} for {mid}")
                elif "data" in result:
                    resolved = result.get("resolvedId", mid)
                    logger.info(f"✅ Download OK (Inline JS): {resolved} ({result.get('size', '?')} bytes)")
                    return base64.b64decode(result["data"])

            # Fallback: try the engine's download_media as a last resort
            logger.warning(f"Inline JS returned nothing. Trying engine fallback for {mid}...")
            for attempt in range(2):
                try:
                    data_b64 = await client.download_media(mid)
                    if data_b64:
                        logger.info(f"✅ Download OK (Engine fallback): {mid}")
                        return base64.b64decode(data_b64)
                except Exception as e:
                    logger.debug(f"Engine fallback attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Fatal error in BridgeDownloader: {e}")

        return None


bridge_downloader = AstraBridge()
