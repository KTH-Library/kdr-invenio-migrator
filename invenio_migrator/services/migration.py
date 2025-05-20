"""Migration service for handling record migration."""

import json
from typing import Any, Dict, Optional

from ..clients.zenodo import ZenodoHarvester
from ..config import CONFIG
from ..utils.logger import logger


class MigrationService:
    """Service for handling migration of records from external sources."""

    def __init__(self):
        """Initialize the migration service."""
        self.logger = logger
        self.harvester = ZenodoHarvester()

    def process_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
    ) -> None:
        """
        Process records from Zenodo based on the provided parameters.

        Args:
            dry_run: If True, fetches records without submitting to KDR.
            query: Optional query string to filter results.
        """
        # Update config with parameters
        if not dry_run:
            dry_run = CONFIG["MIGRATION_OPTIONS"]["DRY_RUN"]

        try:
            self.logger.info("Starting harvesting ...")

            for record in self.harvester.harvest_records(query=query):
                self.logger.info("Fetched record: %s, %s", record["doi"], record["id"])
                if not record:
                    self.logger.warning("No records found for query: %s", query)
                    continue
                self._process_record(record, dry_run)

        except Exception as e:
            self.logger.error("Harvest failed: %s", str(e))
            if CONFIG["MIGRATION_OPTIONS"]["STOP_ON_ERROR"]:
                raise

    def _process_record(self, record: Dict[str, Any], dry_run: bool) -> None:
        """
        Process a single record.

        Args:
            record: The record to process.
            dry_run: If True, just logs the record without processing.
            output: Optional file path to save the record.
        """
        self.logger.info(
            "Processing record ID: %s, with DOI: %s",
            record["id"],
            record.get("doi"),
        )

        if dry_run:
            self.logger.debug("Dry run: Would process %s", record["doi"])
            self.logger.info(json.dumps(record, indent=2))
            return

        # TODO: Add processing logic here
        self.logger.info("Fetched record %s", record["doi"])
