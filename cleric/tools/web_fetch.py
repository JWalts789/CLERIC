"""Web page fetching tool for extracting text content from URLs.

Uses httpx for HTTP requests and BeautifulSoup for HTML parsing,
stripping navigation, scripts, and other non-content elements.
"""

import httpx
from bs4 import BeautifulSoup


FETCH_PAGE_SCHEMA: dict = {
    "name": "fetch_page",
    "description": (
        "Fetch a web page and extract its main text content. Strips navigation, "
        "footers, scripts, and styling. Use this to read the full content of a "
        "page found via web_search."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the web page to fetch.",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum character length of returned text. Defaults to 2000.",
                "default": 2000,
            },
        },
        "required": ["url"],
    },
}

NOISE_TAGS = [
    "script", "style", "nav", "footer", "header", "aside",
    "form", "iframe", "noscript", "svg",
]

REQUEST_HEADERS = {
    "User-Agent": "CLERIC Research Agent/0.1 (educational project)",
    "Accept": "text/html,application/xhtml+xml",
}

REQUEST_TIMEOUT = 15.0


def fetch_page(url: str, max_length: int = 2000) -> str:
    """Fetch a web page and extract its main text content.

    Removes navigation, footers, scripts, styles, and other non-content
    elements, then returns cleaned text truncated to max_length.

    Args:
        url: The URL to fetch.
        max_length: Maximum characters to return.

    Returns:
        Extracted text content, or an error message string on failure.
    """
    if "wikipedia.org" in url.lower():
        return "Wikipedia is blocked as a source. Use primary sources (academic papers, government reports, established journalism) instead."

    try:
        response = httpx.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return f"HTTP error fetching {url}: {e.response.status_code}"
    except httpx.RequestError as e:
        return f"Request failed for {url}: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", {"role": "main"})
        or soup.body
        or soup
    )

    text = main_content.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    if len(text) > max_length:
        text = text[:max_length] + "\n\n[...truncated]"

    return text
