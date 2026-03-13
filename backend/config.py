"""
config.py
---------
Central configuration for the AI-Powered Web Vulnerability Scanner.
All environment-specific and tunable values are defined here.
Import this module wherever settings are needed — never hardcode values.
"""

import os
from dotenv import load_dotenv

# Load values from a .env file if present (useful for local dev)
load_dotenv()


class Config:
    # ------------------------------------------------------------------ #
    # Flask settings
    # ------------------------------------------------------------------ #
    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # ------------------------------------------------------------------ #
    # HTTP client settings
    # ------------------------------------------------------------------ #
    # Seconds to wait for a single HTTP response
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    # How many times to retry a failed request before giving up
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    # User-agent sent with every outgoing request
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (compatible; VulnScanner/1.0; +https://example.com/bot)"
    )

    # ------------------------------------------------------------------ #
    # Crawler settings
    # ------------------------------------------------------------------ #
    # Maximum number of links to follow from the seed URL
    MAX_CRAWL_URLS: int = int(os.getenv("MAX_CRAWL_URLS", "50"))
    # How many link-levels deep the crawler may go (1 = seed page only)
    CRAWL_DEPTH: int = int(os.getenv("CRAWL_DEPTH", "3"))

    # ------------------------------------------------------------------ #
    # AI / ML model settings
    # ------------------------------------------------------------------ #
    # Path to the serialised scikit-learn model file
    MODEL_PATH: str = os.getenv("MODEL_PATH", "data/models/vuln_model.joblib")

    # ------------------------------------------------------------------ #
    # Report storage
    # ------------------------------------------------------------------ #
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "data/scan_reports")

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# A single shared instance imported everywhere
config = Config()
