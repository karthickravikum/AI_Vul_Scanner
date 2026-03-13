"""
controllers/scan_controller.py
-------------------------------
Exposes the POST /api/scan endpoint.

This controller's only job is:
  1. Parse and validate the incoming JSON request
  2. Hand the URL off to the scanner service
  3. Return an HTTP response

No scanning logic lives here.
"""

import logging
from flask import Blueprint, request, jsonify

from services.scanner_service import run_scan
from utils.url_utils import validate_url, normalize_url

logger = logging.getLogger(__name__)

# A Blueprint groups related routes; registered in app.py
scan_bp = Blueprint("scan", __name__)


@scan_bp.post("/scan")
def start_scan():
    """
    POST /api/scan

    Expected JSON body:
        { "url": "https://example.com" }

    Returns:
        201 - scan completed, includes scan_id and summary
        400 - bad request (missing or invalid URL)
        500 - unexpected server error
    """
    body = request.get_json(silent=True)

    # ---- 1. Input validation ----------------------------------------- #
    if not body or "url" not in body:
        return jsonify({"error": "Request body must contain a 'url' field."}), 400

    raw_url: str = body["url"].strip()

    if not validate_url(raw_url):
        return jsonify({"error": f"'{raw_url}' is not a valid HTTP/HTTPS URL."}), 400

    target_url: str = normalize_url(raw_url)
    logger.info("Scan requested for: %s", target_url)

    # ---- 2. Run the scanning pipeline --------------------------------- #
    try:
        scan_result = run_scan(target_url)
    except Exception as exc:
        logger.error("Scan failed for %s: %s", target_url, exc, exc_info=True)
        return jsonify({"error": "An internal error occurred during the scan."}), 500

    # ---- 3. Return a concise response --------------------------------- #
    return jsonify({
        "scan_id":            scan_result.scan_id,
        "target":             scan_result.target,
        "timestamp":          scan_result.timestamp,
        "total_scanned":      scan_result.total_scanned,
        "vulnerability_count": len(scan_result.vulnerabilities),
        "message":            "Scan completed. Use /api/report/<scan_id> for full details."
    }), 201
