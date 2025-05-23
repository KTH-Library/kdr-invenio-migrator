"""Record mappers for converting between different repository formats."""

from typing import Any, Dict, Optional

from invenio_migrator.config import CONFIG  # Added import
from invenio_migrator.errors import RecordMappingError, RecordValidationError
from invenio_migrator.interfaces import BaseRecordMapper
from invenio_migrator.utils.logger import logger
from invenio_migrator.utils.mapper import RELATION_TYPE_MAP


class ZenodoToInvenioRDMMapper(BaseRecordMapper):
    """Maps records from Zenodo format to InvenioRDM format."""

    def map_record(self, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Zenodo record to InvenioRDM format."""
        try:
            record_id = source_record.get("id", "unknown")
            metadata = source_record.get("metadata", {})

            # Map core components
            creators = self._map_creators(metadata.get("creators", []))
            subjects = self._map_subjects(metadata.get("keywords", []))
            resource_type_id = self._map_resource_type(
                metadata.get("resource_type", {})
            )
            related_identifiers = self._map_related_identifiers(
                source_record.get("doi"), metadata
            )
            pids = self._map_pids(source_record)

            # Build the mapped record
            mapped_record = {
                "access": {"record": "public", "files": "public"},
                "files": {"enabled": True},
                # "pids": pids, # Conditionally added below
                "metadata": {
                    "title": metadata.get("title"),
                    "resource_type": {"id": resource_type_id},
                    "description": metadata.get("description"),
                    "creators": creators,
                    "publication_date": metadata.get("publication_date"),
                    "subjects": subjects,
                    "related_identifiers": related_identifiers,
                },
                "type": "community-submission",
            }

            # Conditionally add pids to the mapped_record
            if CONFIG["DRAFT_RECORDS"].get("INCLUDE_PIDS", True):
                mapped_record["pids"] = pids

            # Validate the mapped record
            if not self.validate_mapped_record(mapped_record):
                raise RecordValidationError(
                    record_id=str(record_id),
                    missing_fields=self._get_missing_fields(mapped_record),
                )

            return mapped_record

        except Exception as e:
            if isinstance(e, (RecordMappingError, RecordValidationError)):
                raise
            raise RecordMappingError(
                record_id=str(source_record.get("id", "unknown")), reason=str(e)
            )

    def _map_creators(self, creators: list) -> list:
        """Map creator information from Zenodo to InvenioRDM format."""
        mapped_creators = []

        for creator in creators:
            try:
                mapped_creator = self._map_single_creator(creator)
                mapped_creators.append(mapped_creator)
            except Exception as e:
                logger.warning(f"Failed to map creator {creator}: {e}")
                continue

        return mapped_creators

    def _map_single_creator(self, creator: Dict) -> Dict:
        """Map a single creator from Zenodo to InvenioRDM format."""
        full_name = creator.get("name", "").strip()
        if not full_name:
            raise RecordMappingError(
                record_id="", field="creator.name", reason="Empty name"
            )

        # Parse name
        if "," in full_name:
            family, given = (part.strip() for part in full_name.split(",", 1))
        else:
            parts = full_name.split()
            family = parts[-1] if len(parts) > 1 else parts[0]
            given = " ".join(parts[:-1]) if len(parts) > 1 else None

        person_or_org = {
            "type": "personal",
            "name": full_name,
            "family_name": family,
            "given_name": given,
        }

        # Add ORCID if present
        if orcid := creator.get("orcid"):
            person_or_org["identifiers"] = [{"identifier": orcid, "scheme": "orcid"}]

        # Build result with affiliation
        result = {"person_or_org": person_or_org}
        if affiliation := creator.get("affiliation"):
            result["affiliations"] = [{"name": affiliation}]

        return result

    def _map_subjects(self, keywords: list) -> list:
        """Map keywords to subjects in InvenioRDM format."""
        return [{"subject": keyword} for keyword in keywords if keyword]

    def _map_resource_type(self, resource_type: Dict) -> str:
        """Map resource type to InvenioRDM format."""
        resource_type_mapping = {
            "dataset": "dataset",
            "publication-article": "publication-article",
            "presentation": "presentation",
            "software": "software",
            "poster": "poster",
            "image": "image",
        }

        zenodo_type = resource_type.get("type", "")
        return resource_type_mapping.get(zenodo_type, "dataset")  # Default fallback

    def _map_related_identifiers(self, doi: str, metadata: Dict[str, Any]) -> list:
        """Map related identifiers including the source DOI."""
        if not doi:
            raise RecordMappingError(
                record_id="", field="doi", reason="DOI is required"
            )

        related = []
        if CONFIG["DRAFT_RECORDS"].get("INCLUDE_PIDS", True):
            related.append(
                {
                    "scheme": "doi",
                    "identifier": doi,
                    "relation_type": {
                        "id": "isderivedfrom",
                        "title": {
                            "en": RELATION_TYPE_MAP.get(
                                "isderivedfrom", "Is derived from"
                            )
                        },
                    },
                    "resource_type": {
                        "id": "publication",
                        "title": {"en": "Publication"},
                    },
                }
            )

        # Process existing related identifiers
        existing = metadata.get("related_identifiers", [])
        for item in existing:
            try:
                mapped_item = self._map_single_related_identifier(item)
                if mapped_item:
                    related.append(mapped_item)
            except Exception as e:
                logger.warning(f"Failed to map related identifier {item}: {e}")
                continue

        return related

    def _map_single_related_identifier(self, item: Dict) -> Optional[Dict]:
        """Map a single related identifier."""
        # Extract relation type
        relation_type_id = None
        if "relation" in item:
            relation_type_id = item["relation"].lower()
        elif "relation_type" in item:
            if isinstance(item["relation_type"], str):
                relation_type_id = item["relation_type"].lower()
            elif isinstance(item["relation_type"], dict):
                relation_type_id = item["relation_type"].get("id", "").lower()

        # Validate relation type
        if not relation_type_id or relation_type_id not in RELATION_TYPE_MAP:
            return None

        # Build the mapped identifier
        mapped_item = dict(item)  # Copy original
        mapped_item.pop("relation", None)  # Remove old format

        # Set correct relation_type structure
        mapped_item["relation_type"] = {
            "id": relation_type_id,
            "title": {"en": RELATION_TYPE_MAP[relation_type_id]},
        }

        # Fix resource_type if needed
        if "resource_type" in mapped_item and isinstance(
            mapped_item["resource_type"], str
        ):
            res_id = mapped_item["resource_type"].lower()
            mapped_item["resource_type"] = {
                "id": res_id,
                "title": {"en": res_id.replace("_", " ").capitalize()},
            }

        return mapped_item

    def _map_pids(self, record: Dict[str, Any]) -> Dict:
        """Map persistent identifiers."""
        doi = record.get("doi")
        if not doi:
            raise RecordMappingError(
                record_id=str(record.get("id", "")),
                field="doi",
                reason="DOI is required",
            )

        return {"doi": {"identifier": doi, "provider": "external"}}

    def validate_mapped_record(self, mapped_record: Dict[str, Any]) -> bool:
        """Validate that the mapped record has all required fields."""
        required_top_level = [
            "access",
            "metadata",
        ]  # Removed "pids" as it's now conditional
        if CONFIG["DRAFT_RECORDS"].get("INCLUDE_PIDS", True):
            required_top_level.append("pids")

        required_metadata = ["title", "creators", "resource_type"]

        # Check top-level fields
        missing_top = [
            field for field in required_top_level if field not in mapped_record
        ]
        if missing_top:
            return False

        # Check metadata fields
        metadata = mapped_record.get("metadata", {})
        missing_meta = [field for field in required_metadata if field not in metadata]
        if missing_meta:
            return False

        # Check that title is not empty
        title = metadata.get("title")
        if not title or (isinstance(title, str) and not title.strip()):
            return False

        # Check that creators is not empty
        if not metadata.get("creators", []):
            return False

        return True

    def _get_missing_fields(self, mapped_record: Dict[str, Any]) -> list:
        """Get list of missing required fields."""
        missing = []

        required_top_level = [
            "access",
            "metadata",
        ]  # Removed "pids" as it's now conditional
        if CONFIG["DRAFT_RECORDS"].get("INCLUDE_PIDS", True):
            required_top_level.append("pids")

        for field in required_top_level:
            if field not in mapped_record:
                missing.append(field)

        if "metadata" in mapped_record:
            required_metadata = ["title", "creators", "resource_type"]
            metadata = mapped_record["metadata"]
            for field in required_metadata:
                if field not in metadata:
                    missing.append(f"metadata.{field}")
                elif field == "title":
                    title = metadata[field]
                    if not title or (isinstance(title, str) and not title.strip()):
                        missing.append(f"metadata.{field} (empty)")
                elif field == "creators" and not metadata[field]:
                    missing.append(f"metadata.{field} (empty)")

        return missing
