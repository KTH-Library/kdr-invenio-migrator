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
    # "TARGET_BASE_URL": "https://sandbox.datarepository.kth.se/api",
    "TARGET_API_TOKEN": os.getenv("TARGET_API_TOKEN"),
    # Local KDR community ID
    "INVENIORDM_COMMUNITY_ID": "21f6dd7d-f98d-489e-b658-3db9aa459f13",
    # Sandbox community ID
    # "INVENIORDM_COMMUNITY_ID": "1ef9e2c5-b11b-448f-985f-1d2e21a42095",
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
    },
}
