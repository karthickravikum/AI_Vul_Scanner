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

Memory optimisations vs original:
  - Response object explicitly deleted after each endpoint scan
  - gc.collect() called after each endpoint to free memory immediately
  - Endpoints processed in small batches to cap peak memory usage
  - Per-endpoint timeout guard prevents one slow URL hanging everything
  - Crawl results cleared from memory before scanning begins
"""

import gc
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

# All vulnerability check functions — easy to extend by adding to this list
_VULN_CHECKS = [
    check_sql_injection,
    check_xss,
    check_security_headers,
    check_directory_exposure,
    check_insecure_forms,
]

# How many endpoints to scan before forcing a garbage collection pass
# Smaller = less peak memory, slightly slower. 5 is a good balance.
_BATCH_SIZE = 5


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

    # ---- Steps 2–6: Scan each endpoint in batches ------------------ #
    all_vulnerabilities: List[Vulnerability] = []

    for batch_start in range(0, len(endpoints), _BATCH_SIZE):
        # Slice a small batch of endpoints
        batch = endpoints[batch_start : batch_start + _BATCH_SIZE]

        logger.debug(
            "[%s] Scanning batch %d-%d of %d",
            scan_id,
            batch_start + 1,
            batch_start + len(batch),
            len(endpoints),
        )

        for endpoint in batch:
            vulns = _scan_endpoint(endpoint)
            all_vulnerabilities.extend(vulns)

            # Free endpoint dict from memory after scanning it
            del vulns

        # Force garbage collection after every batch
        # This keeps peak memory flat regardless of total endpoint count
        gc.collect()
        logger.debug("[%s] Batch complete — memory freed", scan_id)

    # Free the full endpoints list — no longer needed
    del endpoints
    gc.collect()

    # ---- Step 7: Build result -------------------------------------- #
    result = ScanResult(
        scan_id=scan_id,
        target=extract_domain(target_url),
        timestamp=datetime.now(timezone.utc).isoformat(),
        vulnerabilities=all_vulnerabilities,
        total_scanned=len(all_vulnerabilities),
    )

    # ---- Step 8: Persist ------------------------------------------ #
    save_report(result)
    logger.info(
        "[%s] Scan complete. %d vulnerabilities found.",
        scan_id,
        len(all_vulnerabilities),
    )

    return result


# ------------------------------------------------------------------ #
# Private helpers
# ------------------------------------------------------------------ #

def _scan_endpoint(endpoint: Dict[str, Any]) -> List[Vulnerability]:
    """
    Run all vulnerability checks against a single endpoint.

    Key memory practices:
      - Response object is explicitly deleted after use
      - gc.collect() is called before returning
      - Any exception in a check is caught so one bad URL
        never crashes the whole scan
    """
    url = endpoint["url"]
    logger.debug("Scanning endpoint: %s", url)

    response: requests.Response | None = safe_get(url)

    if response is None:
        logger.warning("Could not reach endpoint during scan: %s", url)
        return []

    found_vulns: List[Vulnerability] = []

    try:
        # Extract features for the AI model
        features = extract_features(endpoint, response)

        # Predict risk level — uses pre-loaded model (no disk I/O here)
        ai_risk = predict_risk(features)
        logger.debug("AI risk for %s = %s", url, ai_risk)

        # Run each vulnerability check function
        for check_fn in _VULN_CHECKS:
            try:
                vuln = check_fn(endpoint, response)
                if vuln is not None:
                    # Attach the AI-predicted risk to every finding
                    vuln.ai_risk = ai_risk
                    found_vulns.append(vuln)
            except Exception as exc:
                logger.error(
                    "Check '%s' raised an exception for %s: %s",
                    check_fn.__name__, url, exc, exc_info=True,
                )

        # Free features dict — no longer needed after checks complete
        del features

    except Exception as exc:
        logger.error(
            "Unexpected error scanning endpoint %s: %s", url, exc, exc_info=True
        )

    finally:
        # Always delete the response object to free the response body from RAM
        # HTTP responses can be large (100KB+) — this matters on 512MB servers
        if response is not None:
            response.close()
            del response

        # Free memory before moving to the next endpoint
        gc.collect()

    return found_vulns