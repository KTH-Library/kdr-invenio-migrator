"""Utils for logging configuration."""

import logging
import sys
from pathlib import Path

import colorlog

logger = logging.getLogger("invenio_migrator")
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s : %(message)s",
    log_colors={
        "DEBUG": "white",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    datefmt="%Y-%m-%d %H:%M:%S",
)
stdout_handler.setFormatter(stdout_formatter)

file_handler = logging.FileHandler(f"{Path.cwd()}/migrator_logs.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s : %(message)s\n", "%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)
