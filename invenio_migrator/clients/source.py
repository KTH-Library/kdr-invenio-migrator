from typing import Optional

from inveniordm_py.client import InvenioAPI

from invenio_migrator.config import CONFIG
from invenio_migrator.utils.logger import logger


class SourceClient:
    """Client for handling source records."""

    def __init__(self):
        """Initialize the source client with configuration."""
        self.source = CONFIG["SOURCE_BASE_URL"]
        self.community_id = CONFIG["SOURCE_COMMUNITY_ID"]
        self.api_token = CONFIG["SOURCE_API_TOKEN"]
        self.dry_run = CONFIG["MIGRATION_OPTIONS"]["DRY_RUN"]
        self.request_delay = CONFIG["RATE_LIMITS"]["SOURCE_REQUEST_DELAY_SECONDS"]

    def fetch_records(self, query: Optional[str] = None) -> None:
        """
        Fetch records from the source.

        Args:
            query: Optional query string to filter results.
        """
        client = InvenioAPI("https://zenodo.org/api/communities/kth/", self.api_token)
        r = client.records.search(query)
        # Implement the logic to fetch records from the source
        logger.info("Fetching records")
        logger.info(dict(r))
