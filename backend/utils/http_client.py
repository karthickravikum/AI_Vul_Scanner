"""
utils/http_client.py
---------------------
Centralised HTTP client with timeout, retry, and error-handling.

All outgoing HTTP requests in the application should go through
safe_get() rather than calling requests.get() directly.
This ensures consistent behaviour (headers, timeouts, retries)
and prevents unhandled exceptions from crashing the scanner.
"""

import logging
import time
from typing import Optional

import requests

from config import config

logger = logging.getLogger(__name__)

# Shared session for connection pooling and persistent headers
_session = requests.Session()
_session.headers.update({
    "User-Agent": config.USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})


def safe_get(url: str) -> Optional[requests.Response]:
    """
    Perform an HTTP GET with automatic retries and error handling.

    Args:
        url: The URL to fetch.

    Returns:
        A requests.Response object on success, or None on failure.
    """
    last_exc: Optional[Exception] = None

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = _session.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                # Don't raise on 4xx/5xx; let callers inspect the status code
                verify=True,
            )
            logger.debug(
                "GET %s → %d (attempt %d/%d)",
                url, response.status_code, attempt, config.MAX_RETRIES
            )
            return response

        except requests.exceptions.SSLError as exc:
            # SSL errors are unlikely to resolve on retry — fail fast
            logger.warning("SSL error for %s: %s", url, exc)
            return None

        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            logger.warning(
                "Connection error for %s (attempt %d/%d): %s",
                url, attempt, config.MAX_RETRIES, exc
            )

        except requests.exceptions.Timeout as exc:
            last_exc = exc
            logger.warning(
                "Timeout for %s (attempt %d/%d)", url, attempt, config.MAX_RETRIES
            )

        except requests.exceptions.RequestException as exc:
            # Catch-all for any other requests error
            logger.error("Unexpected request error for %s: %s", url, exc)
            return None

        # Exponential back-off between retries (0.5 s, 1 s, 2 s, …)
        if attempt < config.MAX_RETRIES:
            sleep_time = 0.5 * (2 ** (attempt - 1))
            logger.debug("Retrying in %.1fs…", sleep_time)
            time.sleep(sleep_time)

    logger.error(
        "All %d attempts failed for %s. Last error: %s",
        config.MAX_RETRIES, url, last_exc
    )
    return None
