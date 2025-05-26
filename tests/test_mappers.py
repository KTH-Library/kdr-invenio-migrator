"""Test the record mappers functionality."""

import pytest

from invenio_migrator.config import CONFIG  # Added import
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
        # Temporarily set INCLUDE_PIDS to True for this test case
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
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
        assert "pids" in mapped_record
        assert mapped_record["pids"]["doi"]["identifier"] == "10.5281/zenodo.12345"

        # Verify access rights
        assert mapped_record["access"]["record"] == "public"
        assert mapped_record["access"]["files"] == "public"

        # Verify other attributes
        assert mapped_record["files"]["enabled"] is True
        assert mapped_record["type"] == "community-submission"

        # Test case where INCLUDE_PIDS is False
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        mapped_record_no_pids = zenodo_mapper.map_record(minimal_zenodo_record)
        assert "pids" not in mapped_record_no_pids
        # Ensure related_identifiers does not include the source DOI when INCLUDE_PIDS is False
        assert not any(
            item["identifier"] == minimal_zenodo_record["doi"]
            and item["relation_type"]["id"] == "isderivedfrom"
            for item in mapped_record_no_pids["metadata"].get("related_identifiers", [])
        )

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
        assert result3["person_or_org"]["given_name"] == ""

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

        # Test case where INCLUDE_PIDS is True
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
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

        # Test case where INCLUDE_PIDS is False
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        related_no_source_doi = zenodo_mapper._map_related_identifiers(doi, metadata)
        assert len(related_no_source_doi) == 1
        assert related_no_source_doi[0]["identifier"] == "10.5281/zenodo.12346"

    def test_validate_mapped_record(self, zenodo_mapper):
        """Test record validation logic."""
        # Valid record with PIDs
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        valid_record_with_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(valid_record_with_pids) is True

        # Valid record without PIDs
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        valid_record_without_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
        }
        assert zenodo_mapper.validate_mapped_record(valid_record_without_pids) is True

        # Missing top-level field (access) when PIDs are expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        invalid1_with_pids = {
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid1_with_pids) is False

        # Missing top-level field (access) when PIDs are NOT expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        invalid1_without_pids = {
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
        }
        assert zenodo_mapper.validate_mapped_record(invalid1_without_pids) is False

        # Missing metadata field (creators) when PIDs are expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        invalid2_with_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {"title": "Test", "resource_type": {"id": "dataset"}},
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid2_with_pids) is False

        # Missing metadata field (creators) when PIDs are NOT expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        invalid2_without_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {"title": "Test", "resource_type": {"id": "dataset"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid2_without_pids) is False

        # Empty title when PIDs are expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        invalid3_with_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "   ",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid3_with_pids) is False

        # Empty title when PIDs are NOT expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        invalid3_without_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "   ",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
        }
        assert zenodo_mapper.validate_mapped_record(invalid3_without_pids) is False

        # Empty creators when PIDs are expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        invalid4_with_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [],
                "resource_type": {"id": "dataset"},
            },
            "pids": {"doi": {"identifier": "test"}},
        }
        assert zenodo_mapper.validate_mapped_record(invalid4_with_pids) is False

        # Empty creators when PIDs are NOT expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = False
        invalid4_without_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [],
                "resource_type": {"id": "dataset"},
            },
        }
        assert zenodo_mapper.validate_mapped_record(invalid4_without_pids) is False

        # Missing pids field when it is expected
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True
        invalid5_missing_pids = {
            "access": {"record": "public", "files": "public"},
            "metadata": {
                "title": "Test",
                "creators": [{"person_or_org": {"name": "Test"}}],
                "resource_type": {"id": "dataset"},
            },
        }
        assert zenodo_mapper.validate_mapped_record(invalid5_missing_pids) is False

    def test_map_creator_edge_cases(self, zenodo_mapper):
        """Test mapping creators with edge cases that caused API errors."""
        # Test names from the error logs
        test_cases = [
            # Case 1: Single name without comma (like "Ali-MacLachlan")
            {
                "name": "Ali-MacLachlan",
                "expected_family": "Ali-MacLachlan",
                "expected_given": "",
            },
            # Case 2: Name with only comma and no given name
            {
                "name": "Smith,",
                "expected_family": "Smith",
                "expected_given": "",
            },
            # Case 3: Name with comma and whitespace only after comma
            {
                "name": "Johnson, ",
                "expected_family": "Johnson",
                "expected_given": "",
            },
            # Case 4: Complex name with multiple parts but no comma
            {
                "name": "van der Berg",
                "expected_family": "Berg",
                "expected_given": "van der",
            },
            # Case 5: Name like "Holzapfel, Andre"
            {
                "name": "Holzapfel, Andre",
                "expected_family": "Holzapfel",
                "expected_given": "Andre",
            },
            # Case 6: Name like "Ramana R. Avula"
            {
                "name": "Ramana R. Avula",
                "expected_family": "Avula",
                "expected_given": "Ramana R.",
            },
        ]

        for test_case in test_cases:
            creator = {"name": test_case["name"], "affiliation": "Test University"}
            result = zenodo_mapper._map_single_creator(creator)

            assert (
                result["person_or_org"]["family_name"] == test_case["expected_family"]
            ), (
                f"Family name mismatch for '{test_case['name']}': expected '{test_case['expected_family']}', got '{result['person_or_org']['family_name']}'"
            )
            assert (
                result["person_or_org"]["given_name"] == test_case["expected_given"]
            ), (
                f"Given name mismatch for '{test_case['name']}': expected '{test_case['expected_given']}', got '{result['person_or_org']['given_name']}'"
            )
            assert result["person_or_org"]["given_name"] is not None, (
                f"Given name should never be None for '{test_case['name']}'"
            )

    def test_map_creators_from_error_logs(self, zenodo_mapper):
        """Test specific creator names that caused API errors in production."""
        # Names from the actual error logs
        error_log_creators = [
            {
                "name": "Ramana R. Avula",
                "affiliation": "KTH Royal Institute of Technology",
                "orcid": "0000-0001-9672-2689",
            },
            {
                "name": "Tobias J. Oechtering",
                "affiliation": "KTH Royal Institute of Technology",
                "orcid": "0000-0002-0036-9049",
            },
            {
                "name": "Daniel Månsson",
                "affiliation": "KTH Royal Institute of Technology",
                "orcid": "0000-0003-4740-1832",
            },
            {
                "name": "Holzapfel, Andre",
                "affiliation": "KTH Royal Institute of Technology",
                "orcid": "0000-0003-1679-6018",
            },
            {
                "name": "Ali-MacLachlan",
                "affiliation": "Birmingham City University",
                "orcid": "0000-0002-9380-3122",
            },
        ]

        for creator in error_log_creators:
            result = zenodo_mapper._map_single_creator(creator)

            # Ensure all required fields are present and not None
            assert "person_or_org" in result
            assert result["person_or_org"]["name"] == creator["name"]
            assert result["person_or_org"]["type"] == "personal"
            assert result["person_or_org"]["family_name"] is not None
            assert result["person_or_org"]["given_name"] is not None
            assert isinstance(result["person_or_org"]["given_name"], str)

            # Ensure affiliation is mapped
            assert "affiliations" in result
            assert result["affiliations"][0]["name"] == creator["affiliation"]

            # Ensure ORCID is mapped
            assert "identifiers" in result["person_or_org"]
            assert (
                result["person_or_org"]["identifiers"][0]["identifier"]
                == creator["orcid"]
            )
            assert result["person_or_org"]["identifiers"][0]["scheme"] == "orcid"

    def test_map_record_with_problematic_creators(self, zenodo_mapper):
        """Test mapping a complete record with creators that previously caused errors."""
        zenodo_record = {
            "id": "8006451",
            "doi": "10.5281/zenodo.8006451",
            "metadata": {
                "title": "Test Record with Problematic Creators",
                "description": "This record contains creators that caused API errors",
                "publication_date": "2025-05-26",
                "resource_type": {"type": "dataset"},
                "creators": [
                    {
                        "name": "Ramana R. Avula",
                        "affiliation": "KTH Royal Institute of Technology",
                        "orcid": "0000-0001-9672-2689",
                    },
                    {
                        "name": "Tobias J. Oechtering",
                        "affiliation": "KTH Royal Institute of Technology",
                        "orcid": "0000-0002-0036-9049",
                    },
                    {
                        "name": "Daniel Månsson",
                        "affiliation": "KTH Royal Institute of Technology",
                        "orcid": "0000-0003-4740-1832",
                    },
                    {
                        "name": "Holzapfel, Andre",
                        "affiliation": "KTH Royal Institute of Technology",
                        "orcid": "0000-0003-1679-6018",
                    },
                    {
                        "name": "Ali-MacLachlan",
                        "affiliation": "Birmingham City University",
                        "orcid": "0000-0002-9380-3122",
                    },
                ],
                "keywords": ["test", "dataset"],
            },
        }

        # Enable PIDs for this test
        CONFIG["DRAFT_RECORDS"]["INCLUDE_PIDS"] = True

        mapped_record = zenodo_mapper.map_record(zenodo_record)

        # Verify the record was mapped successfully
        assert "metadata" in mapped_record
        assert (
            mapped_record["metadata"]["title"]
            == "Test Record with Problematic Creators"
        )

        # Verify all creators were mapped and have non-null given_name
        creators = mapped_record["metadata"]["creators"]
        assert len(creators) == 5

        for i, creator in enumerate(creators):
            assert "person_or_org" in creator
            assert creator["person_or_org"]["given_name"] is not None
            assert isinstance(creator["person_or_org"]["given_name"], str)

        # Check specific creator mappings
        assert creators[0]["person_or_org"]["family_name"] == "Avula"
        assert creators[0]["person_or_org"]["given_name"] == "Ramana R."

        assert creators[1]["person_or_org"]["family_name"] == "Oechtering"
        assert creators[1]["person_or_org"]["given_name"] == "Tobias J."

        assert creators[2]["person_or_org"]["family_name"] == "Månsson"
        assert creators[2]["person_or_org"]["given_name"] == "Daniel"

        assert creators[3]["person_or_org"]["family_name"] == "Holzapfel"
        assert creators[3]["person_or_org"]["given_name"] == "Andre"

        assert creators[4]["person_or_org"]["family_name"] == "Ali-MacLachlan"
        assert (
            creators[4]["person_or_org"]["given_name"] == ""
        )  # Empty string, not None
