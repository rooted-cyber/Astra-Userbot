# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import asyncio
import logging
from typing import List, Dict, Any, Optional
from googlesearch import search as gsearch
from duckduckgo_search import DDGS

logger = logging.getLogger("Astra.Search")

async def perform_search(query: str, engines: List[str] = ["google"], limit: int = 5) -> Optional[Dict[str, Any]]:
    """
    Performs a web search using standalone Python libraries (googlesearch and duckduckgo-search).
    
    Args:
        query: The search term.
        engines: List of engines to use (e.g. ['google'], ['duckduckgo']).
        limit: Number of results to return.
        
    Returns:
        A dictionary containing 'results', or None if all libraries fail.
    """
    results = []
    engine_used = engines[0] if engines else "google"
    
    try:
        if "google" in engines:
            # googlesearch-python is synchronous, run in thread
            def sync_google():
                # returns a generator of links
                return list(gsearch(query, num_results=limit, advanced=True))
            
            search_results = await asyncio.to_thread(sync_google)
            for res in search_results:
                results.append({
                    "title": res.title,
                    "url": res.url,
                    "content": res.description
                })
            
        elif "duckduckgo" in engines or "ddg" in engines:
            # duckduckgo-search is synchronous, run in thread
            def sync_ddg():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=limit))
            
            search_results = await asyncio.to_thread(sync_ddg)
            for res in search_results:
                results.append({
                    "title": res.get("title"),
                    "url": res.get("href"),
                    "content": res.get("body")
                })
                
        if results:
            return {
                "results": results[:limit],
                "instance": f"Python Lib ({engine_used})"
            }
            
    except Exception as e:
        logger.error(f"Search library error ({engine_used}): {str(e)}")
            
    return None
