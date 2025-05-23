"""Configuration settings for Invenio Migrator."""

import os

from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Zenodo settings
    "SOURCE_BASE_URL": os.getenv("SOURCE_BASE_URL", default="https://zenodo.org/api"),
    "SOURCE_COMMUNITY_ID": os.getenv("SOURCE_COMMUNITY_ID", default="kth"),
    "SOURCE_API_TOKEN": os.getenv("SOURCE_API_TOKEN"),
    # InvenioRDM settings
    "TARGET_BASE_URL": os.getenv(
        "TARGET_BASE_URL", default="https://127.0.0.1:5000/api"
    ),
    # "TARGET_BASE_URL": "https://sandbox.datarepository.kth.se/api",
    "TARGET_API_TOKEN": os.getenv("TARGET_API_TOKEN"),
    "INVENIORDM_COMMUNITY_ID": os.getenv("INVENIORDM_COMMUNITY_ID"),
    "COMMUNITY_REVIEW_CONTENT": "👾👾👾 Auto generated using KDR migration tool 👾👾👾",
    "RATE_LIMITS": {
        "SOURCE_REQUEST_DELAY_SECONDS": 2,
        "INVENIORDM_REQUEST_DELAY_SECONDS": 1,
    },
    "FILE_HANDLING": {
        "DOWNLOAD_FILES": False,
        "DOWNLOAD_PATH": "./migration_files_download",
        "CLEANUP_DOWNLOADED_FILES_AFTER_UPLOAD": True,
    },
    "MIGRATION_OPTIONS": {
        "DRY_RUN": False,
        "STOP_ON_ERROR": False,
    },
    "SESSION": {
        "VERIFY_SSL": False,  # Only for testing!
        "TIMEOUT": 30,
    },
    "DRAFT_RECORDS": {
        "INCLUDE_PIDS": True,
    },
}
