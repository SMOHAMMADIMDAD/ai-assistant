import asyncio
import json
import logging
import os
import re
import textwrap
from typing import Any
from urllib.parse import urldefrag, urlparse

import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
RESEARCH_MODEL = os.getenv("GEMINI_RESEARCH_MODEL", "gemini-2.5-flash")

if not GOOGLE_API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY in your backend .env file.")

client = genai.Client(api_key=GOOGLE_API_KEY)
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
SEARCH_TIMEOUT = 15.0  # Reduced timeout for faster fail/success response

# --- Optimized Performance Limits ---
MAX_QUERIES = 2                 # Reduced from 5 to 2 for faster search execution
MAX_SOURCES = 4                 # Reduced from 10 to 4 for cleaner aggregation
MAX_PAGE_CHARS = 2000           # Capped page text length
MAX_TOTAL_CONTENT_CHARS = 10000 # Smaller payload for faster LLM synthesis


class ResearchServiceError(Exception):
    """Raised when a research step cannot complete reliably."""


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return urldefrag(url)[0]


async def generate_text(prompt: str) -> str:
    """Run the synchronous Gemini SDK call without blocking the event loop."""
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=RESEARCH_MODEL,
            contents=prompt,
        )
        result = getattr(response, "text", None)
        if not result or not result.strip():
            raise ResearchServiceError("Gemini returned an empty response.")
        return result.strip()
    except ResearchServiceError:
        raise
    except Exception as exc:
        logger.exception("Gemini request failed")
        raise ResearchServiceError(
            "Gemini could not complete the research request. Check the model name, API key, and account limits."
        ) from exc


async def generate_search_queries(user_prompt: str) -> list[str]:
    """Create focused web-search queries from the user's research question."""
    instruction = f"""
Create up to {MAX_QUERIES} distinct web-search queries for researching the request below.
Prefer specific, factual queries that cover different important aspects.
Return ONLY a valid JSON array of strings. Do not include markdown fences.

Research request:
{user_prompt}
"""
    raw = await generate_text(instruction)
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            queries = [str(item).strip() for item in parsed if str(item).strip()]
            if queries:
                return queries[:MAX_QUERIES]
    except (json.JSONDecodeError, TypeError):
        logger.warning("Gemini did not return valid JSON search queries; using the original prompt.")
    return [user_prompt.strip()]


async def get_search_results(query: str) -> list[dict[str, Any]]:
    """Search the web through Tavily and normalize results."""
    if not TAVILY_API_KEY:
        raise ResearchServiceError(
            "TAVILY_API_KEY is missing. Add it to the backend .env file and restart the server."
        )

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "topic": "general",
        "search_depth": "basic",  # Use 'basic' instead of 'advanced' for significantly faster response times
        "max_results": 3,         # Reduced from 5 to 3
        "include_raw_content": False,
    }

    try:
        async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT, follow_redirects=True) as http:
            response = await http.post(TAVILY_SEARCH_URL, headers=headers, json=payload)
            if response.is_error:
                logger.error("Tavily search failed with HTTP %s for query %r", response.status_code, query)
                if response.status_code in (401, 403):
                    raise ResearchServiceError("Tavily rejected the API key. Verify TAVILY_API_KEY in .env.")
                if response.status_code == 429:
                    raise ResearchServiceError("Tavily rate or credit limit was reached. Check your Tavily account.")
                raise ResearchServiceError(f"Tavily search returned HTTP {response.status_code}.")

            data = response.json()
            raw_results = data.get("results", []) if isinstance(data, dict) else []
            normalized: list[dict[str, Any]] = []
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                link = normalize_url(str(item.get("url") or item.get("link") or ""))
                if not link:
                    continue
                content = str(item.get("content") or "")
                normalized.append({
                    "title": str(item.get("title") or "Web source"),
                    "link": link,
                    "content": content[:MAX_PAGE_CHARS],
                })
            return normalized
    except ResearchServiceError:
        raise
    except httpx.TimeoutException as exc:
        logger.warning("Tavily search timed out for query %r", query)
        raise ResearchServiceError("Tavily search timed out. Please try again.") from exc
    except httpx.HTTPError as exc:
        logger.exception("Tavily HTTP request failed")
        raise ResearchServiceError(
            "Unable to connect to Tavily. Check your internet connection and try again."
        ) from exc
    except ValueError as exc:
        logger.exception("Tavily returned invalid JSON")
        raise ResearchServiceError("Tavily returned an invalid response.") from exc


async def perform_deep_research(prompt: str) -> dict[str, Any]:
    """
    Research a prompt using Gemini + Tavily (Optimized for Speed).
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ResearchServiceError("Please enter a research question.")

    if not TAVILY_API_KEY:
        raise ResearchServiceError(
            "TAVILY_API_KEY is missing. Add it to the backend .env file and restart the server."
        )

    queries = await generate_search_queries(prompt)
    search_batches = await asyncio.gather(
        *(get_search_results(query) for query in queries),
        return_exceptions=True,
    )

    collected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for batch in search_batches:
        if isinstance(batch, Exception):
            logger.warning("One Tavily search query failed: %s", batch)
            continue
        for item in batch:
            link = item["link"]
            if link not in seen_urls:
                seen_urls.add(link)
                collected.append(item)
            if len(collected) >= MAX_SOURCES:
                break
        if len(collected) >= MAX_SOURCES:
            break

    if not collected:
        raise ResearchServiceError(
            "No usable web sources were found. Try a more specific research question or check Tavily."
        )

    source_sections: list[str] = []
    total_chars = 0
    for index, source in enumerate(collected, start=1):
        content = source.get("content", "").strip()
        if not content:
            content = "No page text was provided by the search service."
        remaining = MAX_TOTAL_CONTENT_CHARS - total_chars
        if remaining <= 0:
            break
        content = content[:remaining]
        total_chars += len(content)
        source_sections.append(
            f"[{index}] {source['title']}\nURL: {source['link']}\nContent:\n{content}"
        )

    synthesis_prompt = textwrap.dedent(f"""
        You are a careful research analyst. Produce a useful, concise research report
        answering the user's request using ONLY the supplied source material.

        Requirements:
        - Start with a concise direct answer or executive summary.
        - Use clear Markdown headings and organized sections.
        - Add inline source citations like [1] or [2] for factual claims.

        User's research request:
        {prompt}

        Web research sources:
        {chr(10).join(source_sections)}
    """).strip()

    report = await generate_text(synthesis_prompt)
    sources = [
        {"title": item["title"], "link": item["link"]}
        for item in collected
    ]
    return {"report": report, "sources": sources}