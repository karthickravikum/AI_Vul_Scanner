"""
models/scan_result.py
----------------------
Data class representing the outcome of a complete website scan.
"""

from dataclasses import dataclass, field
from typing import List

from models.vulnerability import Vulnerability


@dataclass
class ScanResult:
    """
    Aggregated result of scanning all endpoints on a target website.

    Attributes:
        scan_id:         UUID string uniquely identifying this scan run.
        target:          Domain name of the scanned site, e.g. "example.com".
        timestamp:       ISO-8601 UTC timestamp of when the scan completed.
        vulnerabilities: All Vulnerability objects found during the scan.
        total_scanned:   Number of endpoints the crawler discovered and tested.
    """

    scan_id:         str
    target:          str
    timestamp:       str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    total_scanned:   int = 0
