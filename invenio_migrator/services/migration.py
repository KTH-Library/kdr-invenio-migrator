"""Migration service for handling record migration."""

import json
from typing import Any, Dict, Optional

from ..clients.target import TargetClient
from ..clients.zenodo import ZenodoHarvester
from ..config import CONFIG
from ..utils.logger import logger


class MigrationService:
    """Service for handling migration of records from external sources."""

    def __init__(self):
        """Initialize the migration service."""
        self.logger = logger
        self.harvester = ZenodoHarvester()
        self.target_client = TargetClient()

    def process_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        include_files: bool = False,
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

            response = self.harvester.harvest_records(query=query)

            if not response:
                self.logger.warning("No records found for query: %s", query)
                return

            for record in response:
                if not record:
                    self.logger.warning("No records found for query: %s", query)
                    return
                mapped_record = self._process_record(
                    record, dry_run, include_files=include_files
                )
                draft = self.target_client.create_record(mapped_record)

        except Exception as e:
            self.logger.error("Harvest failed: %s", str(e))

    def _process_record(
        self, record: Dict[str, Any], dry_run: bool, include_files: bool
    ) -> None:
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

        self.map_source_to_target(record, include_files=include_files)
        self.tar

        self.logger.info("Record processed successfully.")

    def map_source_to_target(self, record: Dict[str, Any], include_files: bool) -> None:
        """
        Map the source record to the target format.


        Args:
            record: The record to map.
        """
        meta = record["metadata"]

        # Map creators to InvenioRDM format
        creators = []
        for c in meta.get("creators", []):
            creator = {
                "person_or_org": {
                    "type": "personal",
                    "name": c.get("name"),
                    "family_name": c.get("name").split(",")[0]
                    if "," in c.get("name", "")
                    else None,
                    "given_name": c.get("name").split(",")[1].strip()
                    if "," in c.get("name", "")
                    else None,
                }
            }
            # ORCID if present
            if "orcid" in c:
                creator["person_or_org"]["identifiers"] = [
                    {"identifier": c["orcid"], "scheme": "orcid"}
                ]
            # Affiliation if present
            if c.get("affiliation"):
                creator["affiliations"] = [{"name": c["affiliation"]}]
            creators.append(creator)

        # Map subjects/keywords
        subjects = [{"subject": kw} for kw in meta.get("keywords", [])]

        # Map resource_type
        resource_type_id = "dataset"  # fallback
        if "resource_type" in meta:
            if meta["resource_type"].get("type") == "dataset":
                resource_type_id = "dataset"
            elif meta["resource_type"].get("type") == "publication-article":
                resource_type_id = "publication-article"
            # Add more mappings as needed

        # Map license
        license_id = meta.get("license", {}).get("id", "cc-by-4.0")

        # Compose InvenioRDM record
        invenio_record = {
            "access": {"record": "public", "files": "public"},
            "files": {"enabled": include_files},
            "metadata": {
                "title": meta.get("title"),
                "resource_type": {"id": resource_type_id},
                "description": meta.get("description"),
                "creators": creators,
                "publication_date": meta.get("publication_date"),
                "subjects": subjects,
                "rights": [{"id": license_id}],
            },
            "type": "community-submission",  # Change if needed
        }

        return invenio_record
