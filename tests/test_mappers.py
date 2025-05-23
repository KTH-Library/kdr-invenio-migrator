"""Test the record mappers functionality."""

import pytest

from invenio_migrator.errors import RecordMappingError, RecordValidationError
from invenio_migrator.mappers import ZenodoToInvenioRDMMapper
from invenio_migrator.utils.mapper import RELATION_TYPE_MAP


@pytest.fixture
def zenodo_mapper():
    """Fixture to provide a ZenodoToInvenioRDMMapper instance."""
    return ZenodoToInvenioRDMMapper()


@pytest.fixture
def minimal_zenodo_record():
    """Fixture to provide a minimal valid Zenodo record."""
    return {
        "id": "12345",
        "doi": "10.5281/zenodo.12345",
        "metadata": {
            "title": "Test Record",
            "description": "This is a test record",
            "publication_date": "2025-05-23",
            "resource_type": {"type": "dataset"},
            "creators": [
                {
                    "name": "Doe, John",
                    "affiliation": "Test University",
                    "orcid": "0000-0001-2345-6789",
                }
            ],
            "keywords": ["test", "dataset"],
        },
    }


class TestZenodoToInvenioRDMMapper:
    """Test the ZenodoToInvenioRDMMapper class."""

    def test_map_record_minimal(self, zenodo_mapper, minimal_zenodo_record):
        """Test mapping a minimal record with all required fields."""
        mapped_record = zenodo_mapper.map_record(minimal_zenodo_record)

        # Verify core metadata
        assert "metadata" in mapped_record
        assert mapped_record["metadata"]["title"] == "Test Record"
        assert mapped_record["metadata"]["description"] == "This is a test record"
        assert mapped_record["metadata"]["publication_date"] == "2025-05-23"

        # Verify creators
        assert len(mapped_record["metadata"]["creators"]) == 1
        creator = mapped_record["metadata"]["creators"][0]
        assert creator["person_or_org"]["name"] == "Doe, John"
        assert creator["person_or_org"]["family_name"] == "Doe"
        assert creator["person_or_org"]["given_name"] == "John"
        assert creator["affiliations"][0]["name"] == "Test University"
        assert (
            creator["person_or_org"]["identifiers"][0]["identifier"]
            == "0000-0001-2345-6789"
        )
        assert creator["person_or_org"]["identifiers"][0]["scheme"] == "orcid"

        # Verify subjects from keywords
        assert len(mapped_record["metadata"]["subjects"]) == 2
        assert mapped_record["metadata"]["subjects"][0]["subject"] == "test"
        assert mapped_record["metadata"]["subjects"][1]["subject"] == "dataset"

        # Verify resource type
        assert mapped_record["metadata"]["resource_type"]["id"] == "dataset"

        # Verify DOI in related identifiers
        assert len(mapped_record["metadata"]["related_identifiers"]) == 1
        rel_id = mapped_record["metadata"]["related_identifiers"][0]
        assert rel_id["identifier"] == "10.5281/zenodo.12345"
        assert rel_id["scheme"] == "doi"
        assert rel_id["relation_type"]["id"] == "isderivedfrom"

        # Verify PIDs
        assert mapped_record["pids"]["doi"]["identifier"] == "10.5281/zenodo.12345"

        # Verify access rights
        assert mapped_record["access"]["record"] == "public"
        assert mapped_record["access"]["files"] == "public"

        # Verify other attributes
        assert mapped_record["files"]["enabled"] is True
        assert mapped_record["type"] == "community-submission"

    def test_map_record_missing_doi(self, zenodo_mapper):
        """Test mapping fails when DOI is missing."""
        record = {
            "id": "12345",
            "metadata": {
                "title": "Test Record",
                "creators": [{"name": "Doe, John"}],
                "resource_type": {"type": "dataset"},
            },
        }

        with pytest.raises(RecordMappingError) as exc_info:
            zenodo_mapper.map_record(record)

        assert "doi" in str(exc_info.value).lower()

    def test_map_record_missing_title(self, zenodo_mapper, minimal_zenodo_record):
        """Test mapping fails validation when title is missing."""
        minimal_zenodo_record["metadata"].pop("title")

        with pytest.raises(RecordValidationError) as exc_info:
            zenodo_mapper.map_record(minimal_zenodo_record)

        assert "validation failed" in str(exc_info.value).lower()
        assert "title" in exc_info.value.missing_fields[0]

    def test_map_record_empty_creators(self, zenodo_mapper, minimal_zenodo_record):
        """Test mapping fails validation when creators list is empty."""
        minimal_zenodo_record["metadata"]["creators"] = []

        with pytest.raises(RecordValidationError) as exc_info:
            zenodo_mapper.map_record(minimal_zenodo_record)

        assert "validation failed" in str(exc_info.value).lower()
        assert "creators" in str(exc_info.value).lower()

    def test_map_creator_with_various_name_formats(self, zenodo_mapper):
        """Test mapping creators with different name formats."""
        # Test with comma format
        creator1 = {"name": "Doe, John", "affiliation": "Test University"}
        result1 = zenodo_mapper._map_single_creator(creator1)
        assert result1["person_or_org"]["family_name"] == "Doe"
        assert result1["person_or_org"]["given_name"] == "John"

        # Test with space format
        creator2 = {"name": "John Doe", "affiliation": "Test University"}
        result2 = zenodo_mapper._map_single_creator(creator2)
        assert result2["person_or_org"]["family_name"] == "Doe"
        assert result2["person_or_org"]["given_name"] == "John"

        # Test with single name
        creator3 = {"name": "Cher", "affiliation": "Music Industry"}
        result3 = zenodo_mapper._map_single_creator(creator3)
        assert result3["person_or_org"]["family_name"] == "Cher"
        assert result3["person_or_org"]["given_name"] is None

    def test_map_creator_with_empty_name(self, zenodo_mapper):
        """Test mapping creator with empty name raises error."""
        creator = {"name": "", "affiliation": "Test University"}

        with pytest.raises(RecordMappingError) as exc_info:
            zenodo_mapper._map_single_creator(creator)

        assert "empty name" in str(exc_info.value).lower()

    def test_map_subjects(self, zenodo_mapper):
        """Test mapping subjects from keywords."""
        keywords = ["science", "research", "data"]
        subjects = zenodo_mapper._map_subjects(keywords)

        assert len(subjects) == 3
        assert subjects[0]["subject"] == "science"
        assert subjects[1]["subject"] == "research"
        assert subjects[2]["subject"] == "data"

        # Test with empty keywords
        empty_keywords = ["", None, "valid"]
        subjects = zenodo_mapper._map_subjects(empty_keywords)
        assert len(subjects) == 1
        assert subjects[0]["subject"] == "valid"

    def test_map_resource_type(self, zenodo_mapper):
        """Test mapping resource types."""
        # Test known types
        assert zenodo_mapper._map_resource_type({"type": "dataset"}) == "dataset"
        assert (
            zenodo_mapper._map_resource_type({"type": "publication-article"})
            == "publication-article"
        )
        assert zenodo_mapper._map_resource_type({"type": "software"}) == "software"

        # Test unknown type falls back to dataset
        assert zenodo_mapper._map_resource_type({"type": "unknown"}) == "dataset"
        assert zenodo_mapper._map_resource_type({}) == "dataset"

    def test_map_related_identifiers(self, zenodo_mapper):
        """Test mapping related identifiers."""
        doi = "10.5281/zenodo.12345"
        metadata = {
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.12346",
                    "relation": "cites",
                    "scheme": "doi",
                }
            ]
        }

        related = zenodo_mapper._map_related_identifiers(doi, metadata)

        # Should have 2 identifiers: the source DOI and the one from related_identifiers
        assert len(related) == 2

        # Check source DOI mapping
        assert related[0]["identifier"] == doi
        assert related[0]["scheme"] == "doi"
        assert related[0]["relation_type"]["id"] == "isderivedfrom"

        # Check related identifier mapping
        assert related[1]["identifier"] == "10.5281/zenodo.12346"
        assert related[1]["scheme"] == "doi"
        assert related[1]["relation_type"]["id"] == "cites"
        assert related[1]["relation_type"]["title"]["en"] == RELATION_TYPE_MAP["cites"]

    def test_validate_mapped_record(self, zenodo_mapper):
        """Test record validation logic."""
        # Valid record
        valid_record = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(valid_record) is True

        # Missing top-level field
        invalid1 = {
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid1) is False

        # Missing metadata field
        invalid2 = {
            "access": {"record": "public", "files": "public"},
            "metadata": {"title": "Test", "resource_type": {"id": "dataset"}},
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid2) is False

        # Empty title
        invalid3 = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "   ",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid3) is False

        # Empty creators
        invalid4 = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid4) is False
