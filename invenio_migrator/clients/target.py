from typing import Optional

from inveniordm_py.client import InvenioAPI

from ..config import CONFIG
from ..utils.logger import logger


class TargetClient:
    """Client for handling target records."""

    def __init__(self):
        """Initialize the target client with configuration."""
        self.source = CONFIG["SOURCE_BASE_URL"]
        self.community_id = CONFIG["SOURCE_COMMUNITY_ID"]
        self.api_token = CONFIG["SOURCE_API_TOKEN"]
        self.dry_run = CONFIG["MIGRATION_OPTIONS"]["DRY_RUN"]
        self.request_delay = CONFIG["RATE_LIMITS"]["SOURCE_REQUEST_DELAY_SECONDS"]

    def fetch_records(self, query: Optional[str] = None) -> None:
        """
        Fetch records from the target.

        Args:
            query: Optional query string to filter results.
        """
        client = InvenioAPI("https://127.0.0.1:5000/api/", self.api_token, verify=False)
        r = client.records.search(query)
        # Implement the logic to fetch records from the target
        logger.info("Fetching records")
        logger.info(dict(r))
