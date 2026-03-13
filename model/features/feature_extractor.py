"""
features/feature_extractor.py
-------------------------------
Converts raw endpoint metadata (from the web crawler) into a numerical
feature vector that the ML model can consume.

This module is called by the Flask scanner backend during a live scan.
It can also be used standalone for testing or data preparation.

Feature definitions
-------------------
url_length          - Number of characters in the URL path + query string
parameter_count     - Number of distinct query-string parameters
form_present        - 1 if the page contains at least one <form>, else 0
input_fields        - Total number of <input>/<textarea> fields across all forms
special_characters  - Count of characters commonly abused in injections: "'<>;|`$
response_size       - HTTP response body size in bytes
status_code         - HTTP status code (200, 404, 500, etc.)
endpoint_depth      - Number of path segments separated by '/'

The feature ORDER returned by extract_features() must always match the
column order used when the model was trained (see training/train_model.py).
"""

import re
from typing import Any
from urllib.parse import urlparse, parse_qs

# Ordered list — changing this order breaks the trained model
FEATURE_NAMES: list[str] = [
    "url_length",
    "parameter_count",
    "form_present",
    "input_fields",
    "special_characters",
    "response_size",
    "status_code",
    "endpoint_depth",
]

# Characters frequently used in injection payloads
_SPECIAL_CHARS_RE = re.compile(r"""["'<>;|`${}\\]""")


def extract_features(endpoint: dict[str, Any]) -> dict[str, float]:
    """
    Extract a named feature dictionary from endpoint metadata.

    Args:
        endpoint: Dict produced by the web crawler, e.g.:
            {
                "url":           "https://example.com/login.php?id=1&user=admin",
                "forms":         [{"action": "/login", "method": "POST",
                                   "inputs": ["username", "password"]}],
                "response_size": 14500,
                "status_code":   200,
            }

    Returns:
        Ordered dict mapping feature name → numeric value.
        Keys are always in FEATURE_NAMES order.

    Example return value:
        {
            "url_length":          42,
            "parameter_count":      2,
            "form_present":         1,
            "input_fields":         2,
            "special_characters":   1,
            "response_size":    14500,
            "status_code":        200,
            "endpoint_depth":       2,
        }
    """
    url: str          = endpoint.get("url", "")
    forms: list       = endpoint.get("forms", [])
    response_size:int = int(endpoint.get("response_size", 0))
    status_code: int  = int(endpoint.get("status_code", 200))

    parsed    = urlparse(url)
    path      = parsed.path   or ""
    query     = parsed.query  or ""
    full_path = path + ("?" + query if query else "")

    url_length          = len(full_path)
    parameter_count     = len(parse_qs(query))
    form_present        = 1 if forms else 0
    input_fields        = sum(len(f.get("inputs", [])) for f in forms)
    special_characters  = len(_SPECIAL_CHARS_RE.findall(full_path))
    endpoint_depth      = max(0, len([p for p in path.split("/") if p]))

    return {
        "url_length":         url_length,
        "parameter_count":    parameter_count,
        "form_present":       form_present,
        "input_fields":       input_fields,
        "special_characters": special_characters,
        "response_size":      response_size,
        "status_code":        status_code,
        "endpoint_depth":     endpoint_depth,
    }


def features_to_vector(features: dict[str, float]) -> list[float]:
    """
    Convert a named feature dict into an ordered list (model input row).

    The order follows FEATURE_NAMES exactly — this is what the model expects.

    Args:
        features: Dict from extract_features().

    Returns:
        List of floats in FEATURE_NAMES order.
    """
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_endpoint = {
        "url": "https://example.com/admin/login.php?id=1&redirect=/home",
        "forms": [
            {"action": "/admin/login", "method": "POST",
             "inputs": ["username", "password", "csrf_token"]}
        ],
        "response_size": 18_400,
        "status_code": 200,
    }

    feats  = extract_features(sample_endpoint)
    vector = features_to_vector(feats)

    print("Feature dict:")
    for k, v in feats.items():
        print(f"  {k:22s} = {v}")

    print(f"\nFeature vector: {vector}")
