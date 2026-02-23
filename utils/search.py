# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger("Astra.Search")

# List of public SearXNG instances that are known to support JSON
# We will rotate through these if one fails or returns HTML instead of JSON.
SEARX_INSTANCES = [
    "https://searx.be",
    "https://searx.work",
    "https://searx.otter.sh",
    "https://searx.ch",
    "https://paulgo.io",
    "https://priv.au",
    "https://searx.tiekoetter.com",
    "https://search.ononoki.org",
    "https://search.demit.online",
    "https://searx.xyz",
]

async def perform_search(query: str, engines: List[str] = ["google"], limit: int = 5) -> Optional[Dict[str, Any]]:
    """
    Performs a web search using a rotating list of SearXNG instances.
    
    Args:
        query: The search term.
        engines: List of engines to use (e.g. ['google'], ['duckduckgo']).
        limit: Number of results to return.
        
    Returns:
        A dictionary containing 'results', 'answers', and 'infoboxes', or None if all instances fail.
    """
    # Shuffle instances to distribute load and try different ones on each call
    instances = SEARX_INSTANCES.copy()
    random.shuffle(instances)
    
    headers = {
        "User-Agent": "AstraUserbot/1.0 (https://github.com/paman7647/Astra-Userbot)",
        "Accept": "application/json"
    }
    
    category = "general"
    engine_str = ",".join(engines)
    
    for instance in instances:
        url = f"{instance}/search?q={query}&format=json&engines={engine_str}&pageno=1"
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=8) as resp:
                    if resp.status == 200:
                        # Check if content-type is JSON
                        content_type = resp.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            data = await resp.json()
                            if data.get('results'):
                                return {
                                    "results": data.get('results', [])[:limit],
                                    "answers": data.get('answers', []),
                                    "infoboxes": data.get('infoboxes', []),
                                    "instance": instance
                                }
                        else:
                            logger.debug(f"Instance {instance} returned non-JSON content: {content_type}")
                    else:
                        logger.debug(f"Instance {instance} returned status {resp.status}")
        except Exception as e:
            logger.debug(f"Failed to search via {instance}: {str(e)}")
            
    logger.error(f"All SearXNG instances failed for query: {query}")
    return None
