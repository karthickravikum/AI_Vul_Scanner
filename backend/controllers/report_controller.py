"""
controllers/report_controller.py
---------------------------------
Exposes the GET /api/report/<scan_id> endpoint.

Fetches a previously stored scan report and returns it as JSON.
"""

import logging
from flask import Blueprint, jsonify

from services.report_service import load_report

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__)


@report_bp.get("/report/<scan_id>")
def get_report(scan_id: str):
    """
    GET /api/report/<scan_id>

    Path parameter:
        scan_id - the unique identifier returned by POST /api/scan

    Returns:
        200 - full vulnerability report as JSON
        404 - no report found for this scan_id
        500 - unexpected server error
    """
    logger.info("Report requested for scan_id: %s", scan_id)

    try:
        report = load_report(scan_id)
    except FileNotFoundError:
        return jsonify({"error": f"No report found for scan_id '{scan_id}'."}), 404
    except Exception as exc:
        logger.error("Failed to load report %s: %s", scan_id, exc, exc_info=True)
        return jsonify({"error": "Could not retrieve the report."}), 500

    return jsonify(report), 200
