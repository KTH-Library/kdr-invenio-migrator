"""Zenodo API client for harvesting records from a specific community."""

import time
from typing import Any, Dict, Iterator

import requests

from invenio_migrator.utils.logger import logger

from ..config import CONFIG


class ZenodoHarvester:
    """Zenodo API client for harvesting records from a specific community."""

    def __init__(self):
        self.base_url = CONFIG["ZENODO_API_URL"].rstrip("/")
        self.community_id = CONFIG["ZENODO_COMMUNITY_ID"]
        self.token = CONFIG["ZENODO_API_TOKEN"]
        self.request_delay = CONFIG["RATE_LIMITS"]["ZENODO_REQUEST_DELAY_SECONDS"]

    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generic request handler with rate limiting and retries"""
        time.sleep(self.request_delay)

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        try:
            response = requests.get(
                url,
                allow_redirects=True,
                headers=headers,
                params=params,
                verify=False,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", str(e))
            raise

    def harvest_records(self, query: str) -> Iterator[Dict[str, Any]]:
        """Paginate through community records with date filtering"""
        # TODO: fix query to be more flexible
        url = f"{self.base_url}/records?q={query}&sort=bestmatch&page=1&size=10"
        params = {
            "communities": self.community_id,
            "size": 100,
            "sort": "newest",
            "all_versions": True,
        }

        while True:
            data = self._make_request(url, params)

            yield from data["hits"]["hits"]

            if "next" not in data.get("links", {}):
                break

            url = data["links"]["next"]
            params = None  # Next URL already includes parameters
