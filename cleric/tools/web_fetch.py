"""Web page fetching tool for extracting text content from URLs.

Uses httpx for HTTP requests and BeautifulSoup for HTML parsing,
stripping navigation, scripts, and other non-content elements.
"""

import random
import time

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15.0

RETRYABLE_STATUS_CODES = {429, 500, 502, 503}
MAX_RETRIES = 2
RETRY_DELAY = 2.0


def _make_request(url: str) -> httpx.Response:
    """Make an HTTP GET request with retry logic and rotating user agents.

    Retries up to MAX_RETRIES times for transient errors (429, 500, 502, 503).
    Returns 403 errors immediately without retrying.

    Raises:
        httpx.HTTPStatusError: For non-retryable HTTP errors or after retries exhausted.
        httpx.RequestError: For connection-level failures after retries exhausted.
    """
    last_exc: Exception | None = None

    for attempt in range(1 + MAX_RETRIES):
        headers = {**REQUEST_HEADERS, "User-Agent": random.choice(USER_AGENTS)}
        try:
            response = httpx.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 403:
                raise
            if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                last_exc = e
                time.sleep(RETRY_DELAY)
                continue
            raise
        except httpx.RequestError as e:
            if attempt < MAX_RETRIES:
                last_exc = e
                time.sleep(RETRY_DELAY)
                continue
            raise

    raise last_exc  # type: ignore[misc]  # pragma: no cover


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
        response = _make_request(url)
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 403:
            return (
                f"Access denied (403) for {url}. "
                "Use search snippet content instead of full page fetch."
            )
        return f"HTTP error fetching {url}: {status}"
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
