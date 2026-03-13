"""
services/scanner_service.py
----------------------------
The central scanning orchestrator.

Pipeline:
  1. Crawl the target to discover endpoints
  2. For each endpoint, fetch a fresh response
  3. Run all vulnerability checks
  4. Extract AI features
  5. Ask the AI service for a risk prediction
  6. Assemble and persist the scan result

This is the only module that should call other services directly;
controllers interact with the pipeline only through run_scan().
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests

from config import config
from models.scan_result import ScanResult
from models.vulnerability import Vulnerability
from services.crawler_service import crawl
from services.vulnerability_service import (
    check_sql_injection,
    check_xss,
    check_security_headers,
    check_directory_exposure,
    check_insecure_forms,
)
from services.ai_service import predict_risk
from services.report_service import save_report
from utils.http_client import safe_get
from utils.feature_extractor import extract_features
from utils.url_utils import extract_domain

logger = logging.getLogger(__name__)

# All vulnerability check functions in one place — easy to extend
_VULN_CHECKS = [
    check_sql_injection,
    check_xss,
    check_security_headers,
    check_directory_exposure,
    check_insecure_forms,
]


def run_scan(target_url: str) -> ScanResult:
    """
    Execute the full scanning pipeline for the given URL.

    Args:
        target_url: Normalised, validated URL to scan.

    Returns:
        A populated ScanResult containing all discovered vulnerabilities.
    """
    scan_id = str(uuid.uuid4())
    logger.info("[%s] Starting scan for %s", scan_id, target_url)

    # ---- Step 1: Crawl -------------------------------------------- #
    endpoints: List[Dict[str, Any]] = crawl(target_url)
    logger.info("[%s] Crawler found %d endpoints", scan_id, len(endpoints))

    # ---- Steps 2–6: Scan each endpoint ----------------------------- #
    all_vulnerabilities: List[Vulnerability] = []

    for endpoint in endpoints:
        vulns = _scan_endpoint(endpoint)
        all_vulnerabilities.extend(vulns)

    # ---- Step 7: Build result -------------------------------------- #
    result = ScanResult(
        scan_id=scan_id,
        target=extract_domain(target_url),
        timestamp=datetime.now(timezone.utc).isoformat(),
        vulnerabilities=all_vulnerabilities,
        total_scanned=len(endpoints),
    )

    # ---- Step 8: Persist ------------------------------------------ #
    save_report(result)
    logger.info(
        "[%s] Scan complete. %d vulnerabilities across %d endpoints.",
        scan_id, len(all_vulnerabilities), len(endpoints)
    )

    return result


# ------------------------------------------------------------------ #
# Private helpers
# ------------------------------------------------------------------ #

def _scan_endpoint(endpoint: Dict[str, Any]) -> List[Vulnerability]:
    """
    Run all checks against a single endpoint.

    We re-fetch the URL here to get a clean response object.
    The crawler response is not stored to keep memory usage low.
    """
    url = endpoint["url"]
    logger.debug("Scanning endpoint: %s", url)

    response: requests.Response | None = safe_get(url)

    if response is None:
        logger.warning("Could not reach endpoint during scan: %s", url)
        return []

    # Extract features for the AI model
    features = extract_features(endpoint, response)

    # Predict risk level via AI / heuristic
    ai_risk = predict_risk(features)
    logger.debug("AI risk for %s = %s", url, ai_risk)

    # Run each vulnerability check
    found_vulns: List[Vulnerability] = []

    for check_fn in _VULN_CHECKS:
        try:
            result = check_fn(endpoint, response)
            if result is not None:
                # Attach the AI-predicted risk to every finding
                result.ai_risk = ai_risk
                found_vulns.append(result)
        except Exception as exc:
            logger.error(
                "Check '%s' raised an exception for %s: %s",
                check_fn.__name__, url, exc, exc_info=True
            )

    return found_vulns
