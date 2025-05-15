"""Utils for logging configuration."""

import logging

from ..config import CONFIG

logger = logging.getLogger("invenio_migrator")

logging_config = {
    "level": CONFIG["LOGGING"]["LEVEL"],
    "format": CONFIG["LOGGING"]["FORMAT"],
    "handlers": [
        {
            "class": "logging.FileHandler",
            "filename": CONFIG["LOGGING"]["FILE"],
            "formatter": "default",
        },
        {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    ],
}


def setup_logging():
    """Configure logging based on config"""
    logging.basicConfig(
        level=CONFIG["LOGGING"]["LEVEL"],
        format=CONFIG["LOGGING"]["FORMAT"],
        handlers=[
            logging.FileHandler(CONFIG["LOGGING"]["FILE"]),
            logging.StreamHandler(),
        ],
    )
