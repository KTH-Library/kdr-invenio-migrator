"""Migration service for handling record migration."""

from typing import Any, Dict, Optional

from ..clients.target import TargetClient
from ..clients.zenodo import ZenodoHarvester
from ..utils.logger import logger


class MigrationService:
    """Service for handling migration of records from external sources."""

    def __init__(self):
        """Initialize the migration service."""
        self.logger = logger
        self.harvester = ZenodoHarvester()
        self.target_client = TargetClient()
        self.record_mapper = RecordMapper()

    def process_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        include_files: bool = False,
        stop_on_error: bool = True,
    ) -> None:
        self.logger.info("Start harvesting ...")
        # fetch records from Zenodo
        response = self.harvester.harvest_records(query=query)

        if not response:
            self.logger.warning("No records found for query: %s", query)
            return

        for record in response:
            if not record:
                self.logger.warning("Empty record encountered.")
                continue

            if dry_run:
                self.logger.info("Dry run mode: %s", record)
                return

            try:
                draft = self.record_mapper.map_record(
                    record, include_files=include_files
                )
                self.target_client.create_draft(draft)
                self.logger.info("Draft processed: %s", draft["title"])
            except Exception as e:
                self.logger.warning("Draft creation failed: %s", e)
                if stop_on_error:
                    raise
                continue


class RecordMapper:
    """Handles mapping between Zenodo and InvenioRDM formats."""

    def map_creator(self, creator: Dict) -> Dict:
        """
        Map a single creator to the InvenioRDM format.

        Args:
            creator: The creator dictionary from the source record.
        """
        mapped_creator = {
            "person_or_org": {
                "type": "personal",
                "name": creator.get("name"),
                "family_name": creator.get("name").split(",")[0]
                if "," in creator.get("name", "")
                else None,
                "given_name": creator.get("name").split(",")[1].strip()
                if "," in creator.get("name", "")
                else None,
            }
        }
        # ORCID if present
        if "orcid" in creator:
            mapped_creator["person_or_org"]["identifiers"] = [
                {"identifier": creator["orcid"], "scheme": "orcid"}
            ]
        # Affiliation if present
        if creator.get("affiliation"):
            mapped_creator["affiliations"] = [{"name": creator["affiliation"]}]

        return mapped_creator

    def map_subjects(self, keywords: list) -> list:
        """
        Map keywords to subjects.

        Args:
            keywords: List of keywords from the source record.
        """
        return [{"subject": kw} for kw in keywords]

    def map_resource_type(self, resource_type: Dict) -> str:
        """
        Map the resource type to the target format.

        Args:
            resource_type: The resource type dictionary from the source record.
        """
        if resource_type.get("type") == "dataset":
            return "dataset"
        elif resource_type.get("type") == "publication-article":
            return "publication-article"
        # Add more mappings as needed
        return "dataset"  # Default fallback

    def map_license(self, license_info: Dict) -> str:
        """
        Map the license to the target format.

        Args:
            license_info: The license dictionary from the source record.
        """
        # TODO: need to check if license id is valid
        # got some errors with license ids
        return license_info.get("id", "cc-by-4.0")

    def map_related_identifiers(self, doi: str, metadata: Dict[str, Any]) -> list:
        """
        Map related identifiers using the record DOI and existing metadata.

        Args:
            doi: The DOI of the source record.
            metadata: The metadata dictionary from the source record.
        """
        if not doi:
            raise ValueError("DOI is required to map related_identifiers")
        # see ids: https://github.com/inveniosoftware/invenio-rdm-records/blob/v10.9.2/invenio_rdm_records/fixtures/data/vocabularies/relation_types.yaml
        related = [
            {
                "scheme": "doi",
                "identifier": doi,
                "relation_type": {
                    "id": "isderivedfrom",
                    "title": {"en": "Is derived from"},
                },
                "resource_type": {"id": "publication", "title": {"en": "Publication"}},
            }
        ]

        # Normalize any existing related_identifiers from the Zenodo metadata
        existing = metadata.get("related_identifiers", [])
        for item in existing:
            # Make sure structure matches expected format
            if isinstance(item.get("relation_type"), str):
                item["relation_type"] = {
                    "id": item["relation_type"],
                    "title": {"en": item["relation_type"]},
                }
            if isinstance(item.get("resource_type"), str):
                item["resource_type"] = {
                    "id": item["resource_type"],
                    "title": {"en": item["resource_type"]},
                }
            related.append(item)

        return related

    def map_record(self, record: Dict[str, Any], include_files: bool) -> Dict:
        """
        Map the source record to the target format.

        Args:
            record: The record to map.
            include_files: Whether to include file information in the mapping.
        """
        meta = record["metadata"]
        creators = [self.map_creator(c) for c in meta.get("creators", [])]
        subjects = self.map_subjects(meta.get("keywords", []))
        resource_type_id = self.map_resource_type(meta.get("resource_type", {}))
        related_identifiers = self.map_related_identifiers(record.get("doi"), meta)
        # license_id = self.map_license(meta.get("license", {}))
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
                # "rights": [{"id": license_id}],
                "related_identifiers": related_identifiers,
            },
            "type": "community-submission",  # Change if needed
        }

        return invenio_record
