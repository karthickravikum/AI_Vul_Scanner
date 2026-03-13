"""
services/report_service.py
---------------------------
Serialises ScanResult objects to JSON files and loads them back.

Reports are stored as:
    data/scan_reports/<scan_id>.json

This gives the GET /api/report/<scan_id> endpoint a simple persistence
layer without requiring a database.
"""

import json
import logging
import os
from typing import Dict, Any

from config import config
from models.scan_result import ScanResult

logger = logging.getLogger(__name__)


def save_report(result: ScanResult) -> str:
    """
    Serialise a ScanResult to a JSON file.

    Args:
        result: Completed scan result.

    Returns:
        Absolute path of the saved file.
    """
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    file_path = _report_path(result.scan_id)

    report_dict = _to_dict(result)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    logger.info("Report saved: %s", file_path)
    return file_path


def load_report(scan_id: str) -> Dict[str, Any]:
    """
    Load a previously saved report by its scan_id.

    Args:
        scan_id: UUID string returned by the scan endpoint.

    Returns:
        The report as a plain Python dict (ready to JSON-serialise for HTTP).

    Raises:
        FileNotFoundError: If no report exists for this scan_id.
    """
    file_path = _report_path(scan_id)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Report file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ #
# Private helpers
# ------------------------------------------------------------------ #

def _report_path(scan_id: str) -> str:
    """Return the expected file path for a given scan_id."""
    return os.path.join(config.REPORTS_DIR, f"{scan_id}.json")


def _to_dict(result: ScanResult) -> Dict[str, Any]:
    """Convert a ScanResult (and its nested Vulnerability objects) to a dict."""
    return {
        "scan_id":                result.scan_id,
        "target":                 result.target,
        "scan_timestamp":         result.timestamp,
        "total_endpoints_scanned": result.total_scanned,
        "vulnerabilities": [
            {
                "type":           v.vuln_type,
                "endpoint":       v.endpoint,
                "severity":       v.severity,
                "ai_risk":        getattr(v, "ai_risk", "Unknown"),
                "description":    v.description,
                "recommendation": v.recommendation,
            }
            for v in result.vulnerabilities
        ],
    }
