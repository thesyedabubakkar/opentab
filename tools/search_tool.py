import logging
from typing import Any, Dict, List
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

async def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Performs a 100% free web search using DuckDuckGo."""
    try:
        # DDGS provides an asynchronous or synchronous context manager
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })
            return formatted
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        return [{"error": str(e)}]

SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Searches the internet for real-time information, news, websites, and answers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g. 'best Italian restaurants in NYC', 'weather in London')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to retrieve (default 5)"
                }
            },
            "required": ["query"]
        }
    }
}
