import os
import requests
from bs4 import BeautifulSoup
from google import genai
import textwrap
from typing import List, Dict, Any, Optional

# =========================
# Configure API Keys
# =========================
from dotenv import load_dotenv
load_dotenv()

GEN_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if not all([GEN_API_KEY, SEARCH_API_KEY, CX]):
    raise RuntimeError("One or more required environment variables are missing.")

genai.configure(api_key=GEN_API_KEY)
# Using a more capable model for reasoning and complex tasks
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# =========================
# Deep Research Helper Functions
# =========================

def get_search_results(query: str, site_search: str = None) -> List[Dict[str, Any]]:
    """Performs a Google search and returns the top results."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": SEARCH_API_KEY,
        "cx": CX,
        "q": query,
        "num": 5
    }
    if site_search:
        params["siteSearch"] = site_search

    try:
        res = requests.get(url, params=params, timeout=5).json()
        return res.get("items", [])
    except Exception as e:
        print(f"Error during Google Search for '{query}': {e}")
        return []

def scrape_text(url: str) -> str:
    """Fetches and scrapes the text from a given URL."""
    try:
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        # Extract text from p, h1, h2, h3 tags for more comprehensive content
        main_content = " ".join([tag.get_text() for tag in soup.find_all(['p', 'h1', 'h2', 'h3'])])
        return main_content[:2000] # Limit content to avoid overly long prompts
    except Exception as e:
        print(f"Could not fetch content from {url}: {e}")
        return ""

def generate_deep_research_queries(initial_query: str) -> List[str]:
    """Uses the AI model to generate a list of related, specific queries."""
    query_prompt = textwrap.dedent(f"""
    I need to perform a deep research on the following topic: '{initial_query}'.
    Please generate 3-5 specific, related search queries that would help me get a comprehensive overview.
    Provide the queries as a simple list, one per line, without any additional text.
    """)
    try:
        response = model.generate_content(query_prompt)
        queries = response.text.strip().split('\n')
        # Remove any leading numbers or bullets
        return [q.strip(' -*').strip() for q in queries if q]
    except Exception as e:
        print(f"Error generating queries: {e}")
        return [initial_query] # Fallback to the original query

def deep_research(initial_query: str) -> str:
    """Performs a multi-step deep research and summarization."""
    # Step 1: Generate a set of comprehensive queries
    queries = generate_deep_research_queries(initial_query)

    # Use the original query if the AI couldn't generate new ones
    if not queries:
        queries = [initial_query]

    all_contents = []
    all_links = []

    print(f"Initial Query: '{initial_query}'")
    print("Generated deep research queries:")
    for q in queries:
        print(f"- {q}")

    # Step 2: Execute all queries and scrape content
    for query in queries:
        results = get_search_results(query)
        for r in results[:2]: # Get top 2 results per query
            content = scrape_text(r["link"])
            if content:
                all_contents.append(f"Source: {r['title']}\nContent: {content}\n")
                all_links.append(r)

    if not all_contents:
        return "No relevant content found for the deep research."

    combined_content = "\n\n---\n\n".join(all_contents)

    # Step 3: Summarize all content with the Gemini API
    summary_prompt = textwrap.dedent(f"""
    You are an expert research analyst. Based on the following information from multiple sources, provide a comprehensive and detailed report.
    Structure your response with clear headings and bullet points.

    Original Research Topic: '{initial_query}'

    Information from Sources:
    {combined_content}
    """)

    try:
        response = model.generate_content(summary_prompt)
        summary_text = response.text
        source_links_str = "\n".join([f"- {r['title']} ({r['link']})" for r in all_links])

        return f"AI Deep Research Report:\n{summary_text}\n\nSources:\n{source_links_str}"
    except Exception as e:
        return f"Error during summarization with Gemini API: {e}"

# =========================
# Main Execution
# =========================
if __name__ == "__main__":
    query = "latest news about the EU AI Act"
    final_report = deep_research(query)
    print("\n--------------------------")
    print(final_report)
    print("--------------------------")
