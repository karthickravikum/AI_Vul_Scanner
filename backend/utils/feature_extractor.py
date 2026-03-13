"""
utils/feature_extractor.py
---------------------------
Extracts numerical features from a crawled endpoint + HTTP response.

These features are fed directly into the AI model (or the fallback
heuristic) in services/ai_service.py.

Keeping feature extraction in its own module means:
  - The AI service stays clean (just prediction logic)
  - Features can be evolved independently
  - Features can be logged / inspected easily
"""

import logging
import re
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)

# Characters often abused in injection attacks
_SPECIAL_CHARS_PATTERN = re.compile(r"[\"'<>;&|`${}\\]")


def extract_features(
    endpoint: Dict[str, Any],
    response: requests.Response,
) -> Dict[str, Any]:
    """
    Build a feature dictionary for a single endpoint.

    Args:
        endpoint: Dict produced by crawler_service, containing at minimum:
                  "url", "forms", "status_code", "response_size"
        response: The HTTP response for the endpoint URL.

    Returns:
        Dict mapping feature name → numeric value.
    """
    url: str = endpoint.get("url", "")
    parsed   = urlparse(url)
    params   = parse_qs(parsed.query)

    # ----- URL-level features ----------------------------------------- #
    url_length        = len(url)
    num_parameters    = len(params)
    num_special_chars = len(_SPECIAL_CHARS_PATTERN.findall(url))

    # ----- Form-level features ---------------------------------------- #
    forms = endpoint.get("forms", [])
    all_inputs = [
        inp
        for form in forms
        for inp in form.get("inputs", [])
    ]
    num_input_fields  = len(all_inputs)
    has_forms         = int(len(forms) > 0)
    has_password_field = int(
        any("password" in inp.lower() or "passwd" in inp.lower() for inp in all_inputs)
    )

    # ----- Response-level features ------------------------------------ #
    status_code   = response.status_code
    response_size = len(response.content)

    features = {
        "url_length":          url_length,
        "num_parameters":      num_parameters,
        "num_special_chars":   num_special_chars,
        "num_input_fields":    num_input_fields,
        "has_forms":           has_forms,
        "has_password_field":  has_password_field,
        "status_code":         status_code,
        "response_size":       response_size,
    }

    logger.debug("Features for %s: %s", url, features)
    return features
