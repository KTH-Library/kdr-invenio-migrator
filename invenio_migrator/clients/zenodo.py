"""Zenodo API client for harvesting records from a specific community."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Iterator

import requests

from ..config import CONFIG

logger = logging.getLogger(__name__)


class ZenodoHarvester:
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
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", str(e))
            raise

    def _parse_record_date(self, record: Dict[str, Any]) -> datetime:
        """Parse publication date from Zenodo record"""
        date_str = record["metadata"]["publication_date"]
        return datetime.strptime(date_str, "%Y-%m-%d")

    def _is_record_in_date_range(self, record: Dict[str, Any]) -> bool:
        """Check if record falls within configured date range"""
        record_date = self._parse_record_date(record)
        start_date = datetime.strptime(CONFIG["START_DATE"], "%Y-%m-%d")
        end_date = datetime.strptime(CONFIG["END_DATE"], "%Y-%m-%d")
        return start_date <= record_date <= end_date

    def harvest_records(self) -> Iterator[Dict[str, Any]]:
        """Paginate through community records with date filtering"""
        url = f"{self.base_url}/records"
        params = {
            "communities": self.community_id,
            "size": 100,
            "sort": "newest",
            "all_versions": True,
        }

        while True:
            data = self._make_request(url, params)

            for record in data["hits"]["hits"]:
                if self._is_record_in_date_range(record):
                    yield record
                else:
                    logger.debug("Skipping record %s outside date range", record["id"])

            if "next" not in data.get("links", {}):
                break

            url = data["links"]["next"]
            params = None  # Next URL already includes parameters
