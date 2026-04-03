"""Web search tool using DuckDuckGo.

Provides agents with the ability to search the web for information
without requiring API keys or rate-limited services.
"""

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


SEARCH_WEB_SCHEMA: dict = {
    "name": "web_search",
    "description": (
        "Search the web using DuckDuckGo. Returns titles, URLs, and snippets "
        "for matching results. Use this to find current information, verify "
        "claims, or discover sources on a topic."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return. Defaults to 10.",
                "default": 10,
            },
        },
        "required": ["query"],
    },
}


def search_web(query: str, max_results: int = 10) -> str:
    """Search the web using DuckDuckGo and return formatted results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        Formatted string with numbered results containing title, URL, and snippet.
        Returns an error message string if the search fails.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("href", "No URL")
            snippet = result.get("body", "No snippet")
            formatted.append(f"[{i}] {title}\n    URL: {url}\n    {snippet}")

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search failed for '{query}': {e}"
