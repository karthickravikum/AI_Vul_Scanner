"""
utils/logger.py
----------------
Central logging configuration.

Call setup_logger() once at application startup (in app.py).
All other modules then use standard logging.getLogger(__name__)
and automatically inherit this configuration.
"""

import logging
import sys

from config import config


def setup_logger() -> None:
    """
    Configure the root logger.

    - Outputs to stdout (captured by most production log aggregators)
    - Uses the format and level defined in config.py
    - Quiets overly verbose third-party libraries
    """
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    # Avoid adding duplicate handlers if setup_logger() is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("bs4").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised at level %s", config.LOG_LEVEL
    )
