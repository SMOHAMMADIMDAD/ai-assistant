import httpx
import logging
from typing import List, Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

class WebSearcher:
    """A service to perform web searches using Google Custom Search API."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        # FIX: Check for Google Custom Search API keys instead
        if not settings.GOOGLE_SEARCH_API_KEY or not settings.GOOGLE_SEARCH_ENGINE_ID:
            logger.warning("⚠️ Google Custom Search API keys not set. Skipping web search.")
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": settings.GOOGLE_SEARCH_API_KEY,
            "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": 3  # Get top 3 results
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "link": item.get("link")
                })

            return results
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching search results: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during web search: {e}")
            return []
