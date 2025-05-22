"""Migration service for handling record migration."""

from typing import Any, Dict, Optional

from ..clients.target import TargetClient
from ..clients.zenodo import ZenodoHarvester
from ..config import CONFIG
from ..utils.logger import logger
from ..utils.mapper import RELATION_TYPE_MAP


class MigrationService:
    """Service for handling migration of records from external sources."""

    def __init__(self):
        """Initialize the migration service."""
        self.logger = logger
        self.source = ZenodoHarvester()
        self.target_client = TargetClient()
        self.record_mapper = RecordMapper()

    def process_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        include_files: bool = False,
    ) -> None:
        stop_on_error = CONFIG["MIGRATION_OPTIONS"]["STOP_ON_ERROR"]
        self.logger.info("Start harvesting ...")
        # fetch records from Zenodo
        response = self.source.harvest_records(query=query)

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
                draft_body = self.record_mapper.map_record(
                    record, include_files=include_files
                )
                draft = self.target_client.create_draft(draft_body)
                self.logger.debug("Draft body: %s", draft_body)

                # create review request
                self.target_client.create_review_request(
                    draft_id=draft.data._data["id"],
                    community_id=CONFIG["INVENIORDM_COMMUNITY_ID"],
                )
                self.target_client.submit_review(
                    draft_id=draft.data._data["id"],
                    content=CONFIG["COMMUNITY_REVIEW_CONTENT"],
                )
            except Exception as e:
                self.logger.warning("Draft creation failed: %s", e)
                if stop_on_error:
                    raise
                continue


class RecordMapper:
    """Handles mapping between Zenodo and InvenioRDM formats."""

    def map_creator(self, creator: Dict) -> Dict:
        full = creator.get("name", "").strip()

        # Name parsing
        if "," in full:
            family, given = (part.strip() for part in full.split(",", 1))
        else:
            parts = full.split()
            family = parts[-1] if len(parts) > 1 else parts[0]
            given = " ".join(parts[:-1]) if len(parts) > 1 else None

        person_or_org = {
            "type": "personal",
            "name": full,
            "family_name": family,
            "given_name": given,
        }

        # Add ORCID if present
        if orcid := creator.get("orcid"):
            person_or_org["identifiers"] = [{"identifier": orcid, "scheme": "orcid"}]

        # Build result and add affiliation if present
        return {
            "person_or_org": person_or_org,
            **(
                {"affiliations": [{"name": aff}]}
                if (aff := creator.get("affiliation"))
                else {}
            ),
        }

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
        if not doi:
            raise ValueError("DOI is required to map related_identifiers")

        related = [
            {
                "scheme": "doi",
                "identifier": doi,
                "relation_type": {
                    "id": "isderivedfrom",
                    "title": {
                        "en": RELATION_TYPE_MAP.get("isderivedfrom", "Is derived from")
                    },
                },
                "resource_type": {"id": "publication", "title": {"en": "Publication"}},
            }
        ]

        existing = metadata.get("related_identifiers", [])
        for item in existing:
            # Map 'relation' to 'relation_type'
            relation_type_id = None
            if "relation" in item:
                relation_type_id = item["relation"].lower()
                item.pop("relation")
            elif "relation_type" in item:
                if isinstance(item["relation_type"], str):
                    relation_type_id = item["relation_type"].lower()
                elif isinstance(item["relation_type"], dict):
                    relation_type_id = item["relation_type"].get("id", "").lower()
            # Validate
            if not relation_type_id or relation_type_id not in RELATION_TYPE_MAP:
                continue  # skip unknown/invalid types

            # Set correct structure
            item["relation_type"] = {
                "id": relation_type_id,
                "title": {"en": RELATION_TYPE_MAP[relation_type_id]},
            }

            # Fix resource_type if needed
            if "resource_type" in item and isinstance(item["resource_type"], str):
                res_id = item["resource_type"].lower()
                item["resource_type"] = {
                    "id": res_id,
                    "title": {"en": res_id.replace("_", " ").capitalize()},
                }

            related.append(item)

        return related

    def map_pids(self, record: Dict[str, Any]) -> Optional[Dict]:
        """
        Map the PID from the source record to the target format.

        Args:
            record: The record to map.
        """
        if not record.get("doi"):
            raise ValueError("DOI is required to map PIDs")
        doi = {"doi": {"identifier": record["doi"], "provider": "external"}}

        return doi

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
        doi = self.map_pids(record)
        # license_id = self.map_license(meta.get("license", {}))
        invenio_record = {
            "access": {"record": "public", "files": "public"},
            "files": {"enabled": include_files},
            "pids": doi,
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
            "type": "community-submission",
        }

        return invenio_record
