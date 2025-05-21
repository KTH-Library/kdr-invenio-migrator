"""Configuration settings for Invenio Migrator."""

import os

from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Zenodo settings
    "SOURCE_BASE_URL": "https://zenodo.org/api",
    "SOURCE_COMMUNITY_ID": "kth",  # Replace with your Zenodo community ID
    "SOURCE_API_TOKEN": os.getenv("SOURCE_API_TOKEN"),
    # InvenioRDM settings
    "TARGET_BASE_URL": "https://127.0.0.1:5000/api",
    "TARGET_API_TOKEN": os.getenv("TARGET_API_TOKEN"),
    # "INVENIORDM_COMMUNITY_ID": "c9caea1c-c355-40d0-b285-9ebc797835ff",
    "INVENIORDM_COMMUNITY_ID": "kth-community-on-zenodo",
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
}
