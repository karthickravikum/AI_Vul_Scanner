"""
utils/url_utils.py
-------------------
Helper functions for URL validation, normalisation, and parsing.
"""

import re
from urllib.parse import urlparse, urlunparse


def validate_url(url: str) -> bool:
    """
    Return True if the URL is a valid http or https address.

    Checks:
      - Scheme must be http or https
      - Must contain a non-empty host/domain
      - Basic structural validity via regex

    Args:
        url: Raw string supplied by the user.

    Returns:
        True if valid, False otherwise.
    """
    if not url:
        return False

    # Quick scheme check before the heavier regex
    if not url.lower().startswith(("http://", "https://")):
        return False

    # RFC-3986 inspired pattern — good enough for practical URL validation
    pattern = re.compile(
        r"^https?://"                    # scheme
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)"  # subdomains
        r"+[A-Z]{2,63}"                  # TLD
        r"(?::\d{1,5})?"                 # optional port
        r"(?:/[^\s]*)?$",                # optional path
        re.IGNORECASE,
    )

    return bool(pattern.match(url))


def normalize_url(url: str) -> str:
    """
    Normalise a URL for consistent internal use.

    Actions:
      - Strip leading/trailing whitespace
      - Lowercase the scheme and host
      - Remove trailing slash from the path root (but not sub-paths)

    Args:
        url: A validated URL string.

    Returns:
        Normalised URL string.
    """
    parsed = urlparse(url.strip())

    # Lowercase scheme and host; keep path case as-is
    normalised = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
    )

    result = urlunparse(normalised)

    # Remove trailing slash only when there's no path beyond "/"
    if result.endswith("/") and result.count("/") == 2:
        result = result.rstrip("/")

    return result


def extract_domain(url: str) -> str:
    """
    Return the domain/netloc portion of a URL.

    Example:
        "https://www.example.com/page?q=1" → "www.example.com"

    Args:
        url: Any URL string.

    Returns:
        The netloc (host + optional port) as a string.
    """
    return urlparse(url).netloc
