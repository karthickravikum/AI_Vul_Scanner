"""
services/crawler_service.py
----------------------------
Crawls a target website and returns a list of discovered endpoints.

Strategy:
  - Start from the seed URL
  - Follow internal links up to CRAWL_DEPTH levels deep
  - Cap total URLs at MAX_CRAWL_URLS to prevent runaway scans
  - Record any HTML forms (action + method) as separate endpoints

Returns a list of dicts, each representing one discovered endpoint.
"""

import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from config import config
from utils.http_client import safe_get

logger = logging.getLogger(__name__)


def crawl(seed_url: str) -> List[Dict[str, Any]]:
    """
    Crawl the website starting from seed_url.

    Args:
        seed_url: The root URL to start crawling from.

    Returns:
        A list of endpoint dicts, e.g.:
        [
            {"url": "https://example.com/login", "forms": [...], "source": "link"},
            ...
        ]
    """
    base_domain = urlparse(seed_url).netloc

    # Sets keep track of what we've visited and what's still queued
    visited:  set[str] = set()
    queue:    List[tuple[str, int]] = [(seed_url, 0)]  # (url, current_depth)
    endpoints: List[Dict[str, Any]] = []

    while queue and len(visited) < config.MAX_CRAWL_URLS:
        url, depth = queue.pop(0)

        if url in visited:
            continue
        visited.add(url)

        logger.debug("Crawling [depth=%d]: %s", depth, url)
        response = safe_get(url)

        if response is None:
            logger.warning("Skipping unreachable URL: %s", url)
            continue

        # Parse the page and extract useful information
        soup = BeautifulSoup(response.text, "html.parser")
        forms = _extract_forms(soup, url)

        endpoints.append({
            "url":           url,
            "status_code":   response.status_code,
            "response_size": len(response.content),
            "forms":         forms,
        })

        # Don't follow links beyond the configured depth
        if depth >= config.CRAWL_DEPTH:
            continue

        # Discover and queue new internal links
        for link_url in _extract_links(soup, url, base_domain):
            if link_url not in visited:
                queue.append((link_url, depth + 1))

    logger.info("Crawl complete. Discovered %d endpoints.", len(endpoints))
    return endpoints


# ------------------------------------------------------------------ #
# Private helpers
# ------------------------------------------------------------------ #

def _extract_links(
    soup: BeautifulSoup,
    current_url: str,
    base_domain: str
) -> List[str]:
    """
    Find all <a href="..."> tags and return only internal absolute URLs.
    External links (different domain) are ignored.
    """
    links: List[str] = []

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"].strip()

        # Build an absolute URL (handles relative paths like /about)
        absolute = urljoin(current_url, href)
        parsed   = urlparse(absolute)

        # Keep only http/https links on the same domain
        if parsed.scheme in ("http", "https") and parsed.netloc == base_domain:
            # Strip fragment (#section) to avoid duplicates
            clean = absolute.split("#")[0]
            if clean:
                links.append(clean)

    return links


def _extract_forms(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
    """
    Find all <form> elements on the page and return structured info.

    Each form dict includes:
        - action: resolved absolute URL the form submits to
        - method: HTTP method (GET or POST)
        - inputs: list of input field names
    """
    forms: List[Dict[str, Any]] = []

    for form in soup.find_all("form"):
        action = form.get("action", "")
        method = form.get("method", "get").upper()

        # Resolve relative form actions against the current page URL
        absolute_action = urljoin(page_url, action) if action else page_url

        inputs = [
            inp.get("name", "")
            for inp in form.find_all(["input", "textarea", "select"])
            if inp.get("name")
        ]

        forms.append({
            "action": absolute_action,
            "method": method,
            "inputs": inputs,
        })

    return forms
