"""Configuration settings for Invenio Migrator."""

import os

CONFIG = {
    # Zenodo settings
    "ZENODO_API_URL": "https://zenodo.org/api/",
    "ZENODO_COMMUNITY_ID": "kth",  # Replace with your Zenodo community ID
    "ZENODO_API_TOKEN": os.getenv("ZENODO_API_TOKEN"),
    # InvenioRDM settings
    "INVENIORDM_API_URL": "https://your-invenio-instance.org/api/",
    "KDR_API_TOKEN": os.getenv("KDR_API_TOKEN"),
    "INVENIORDM_COMMUNITY_ID": "target-community-id",
    "RATE_LIMITS": {
        "ZENODO_REQUEST_DELAY_SECONDS": 2,
        "INVENIORDM_REQUEST_DELAY_SECONDS": 1,
    },
    "FILE_HANDLING": {
        "DOWNLOAD_FILES": False,
        "DOWNLOAD_PATH": "./migration_files_download",
        "CLEANUP_DOWNLOADED_FILES_AFTER_UPLOAD": True,
    },
    "MIGRATION_OPTIONS": {
        "DRY_RUN": False,
        "MAX_RECORDS_TO_PROCESS": 2,
        "STOP_ON_ERROR": False,
        "COMPARE_VERSIONS_STRICTLY": False,
    },
}
