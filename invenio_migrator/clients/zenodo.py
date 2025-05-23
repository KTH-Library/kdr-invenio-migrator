"""Zenodo API client for harvesting records from a specific community."""

import time
from typing import Any, Dict, Iterator, Optional

import requests

from invenio_migrator.config import CONFIG
from invenio_migrator.errors import APIClientError, AuthenticationError
from invenio_migrator.interfaces import BaseAPIClient, RecordProviderInterface
from invenio_migrator.utils.logger import logger


class ZenodoClient(BaseAPIClient, RecordProviderInterface):
    """Zenodo API client implementing provider interface."""

    def __init__(self):
        super().__init__(
            base_url=CONFIG["SOURCE_BASE_URL"], api_token=CONFIG["SOURCE_API_TOKEN"]
        )
        self.community_id = CONFIG["SOURCE_COMMUNITY_ID"]
        self.request_delay = CONFIG["RATE_LIMITS"]["SOURCE_REQUEST_DELAY_SECONDS"]
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup the HTTP session with authentication and headers."""
        self._session = requests.Session()
        if self.api_token:
            self._session.headers.update({"Authorization": f"Bearer {self.api_token}"})
        self._session.verify = False  # Only for testing
        self._session.timeout = 30

    def make_request(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request to the Zenodo API with rate limiting and error handling."""
        time.sleep(self.request_delay)

        try:
            response = self._session.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid Zenodo API token")
            raise APIClientError(
                f"Zenodo API request failed: {e}",
                status_code=e.response.status_code,
                response_data=e.response.json() if e.response.content else None,
            )
        except requests.exceptions.RequestException as e:
            raise APIClientError(f"Request failed: {str(e)}")

    def get_records(
        self, query: Optional[str] = None, **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """Get records from Zenodo with pagination support."""
        if not query:
            query = "*"

        url = f"{self.base_url}/records"
        params = {
            "q": query,
            "communities": self.community_id,
            "size": kwargs.get("size", 100),
            "sort": kwargs.get("sort", "newest"),
            "all_versions": kwargs.get("all_versions", True),
        }

        while url:
            data = self.make_request(url, params=params)

            # Yield records from current page
            yield from data.get("hits", {}).get("hits", [])

            # Get next page URL
            links = data.get("links", {})
            url = links.get("next")
            params = None  # Next URL already includes parameters

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        url = f"{self.base_url}/records/{record_id}"
        try:
            return self.make_request(url)
        except APIClientError as e:
            if e.status_code == 404:
                logger.warning(f"Record {record_id} not found")
                return None
            raise

    # Backward compatibility
    def harvest_records(self, query: str) -> Iterator[Dict[str, Any]]:
        """Legacy method for backward compatibility."""
        logger.warning("harvest_records is deprecated, use get_records instead")
        return self.get_records(query=query)

    def get_record_count(self, query: Optional[str] = None) -> int:
        """Get the total count of records matching the query."""
        if not query:
            query = "*"

        url = f"{self.base_url}/records"
        params = {
            "q": query,
            "communities": self.community_id,
            "size": 1,  # We only need count, not actual records
        }

        try:
            data = self.make_request(url, params=params)
            return data.get("hits", {}).get("total", 0)
        except APIClientError as e:
            logger.error(f"Failed to get record count: {str(e)}")
            return 0

    def validate_connection(self) -> bool:
        """Validate the connection to the Zenodo API."""
        try:
            # Try to fetch a small amount of data to verify connection
            url = f"{self.base_url}/records"
            params = {
                "q": "*",
                "communities": self.community_id,
                "size": 1,
            }
            self.make_request(url, params=params)
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            return False


# Backward compatibility alias
ZenodoHarvester = ZenodoClient
