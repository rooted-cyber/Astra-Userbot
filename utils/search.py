# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import asyncio
import logging
from typing import List, Dict, Any, Optional
from ddgs import DDGS

logger = logging.getLogger("Astra.Search")

async def perform_search(query: str, engines: List[str] = ["google"], limit: int = 5) -> Optional[Dict[str, Any]]:
    """
    Performs a web search using the DDGS library.
    
    Note: Both 'google' and 'duckduckgo' currently use DDGS for reliability,
    as direct scraping of Google is often blocked.
    """
    results = []
    engine_used = engines[0] if engines else "google"
    
    def _fetch_ddgs():
        try:
            with DDGS() as ddgs:
                # In ddgs v9.10.0, the argument is 'query' (positional)
                return list(ddgs.text(query, max_results=limit))
        except Exception as e:
            logger.error(f"Search Engine Error: {e}")
            return []

    try:
        search_results = await asyncio.to_thread(_fetch_ddgs)
        
        for res in search_results:
            results.append({
                "title": res.get("title", "No Title"),
                "url": res.get("href", "#"),
                "content": res.get("body", "")
            })
            
        if results:
            return {
                "results": results[:limit],
                "instance": f"Python Lib ({engine_used})"
            }
            
    except Exception as e:
        logger.error(f"Search utility execution error: {str(e)}")
            
    return None
