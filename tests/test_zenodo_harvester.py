"""Test the Zenodo harvester functionality (for legacy code compatibility)."""

from unittest.mock import MagicMock, patch

import pytest

from invenio_migrator.clients.zenodo import ZenodoClient, ZenodoHarvester


@pytest.fixture
def mock_zenodo_harvester():
    """Fixture to provide a mocked ZenodoHarvester (legacy class)."""
    with patch(
        "invenio_migrator.clients.zenodo.CONFIG",
        {
            "SOURCE_BASE_URL": "https://zenodo.example.org/api",
            "SOURCE_API_TOKEN": "test-token",
            "SOURCE_COMMUNITY_ID": "test-community",
            "RATE_LIMITS": {"SOURCE_REQUEST_DELAY_SECONDS": 0},
        },
    ):
        harvester = ZenodoHarvester()
        harvester._session = MagicMock()
        return harvester


def test_legacy_class():
    """Test that ZenodoHarvester is an alias of ZenodoClient."""
    assert ZenodoHarvester is ZenodoClient


def test_harvest_records(
    mock_zenodo_harvester, sample_zenodo_record, mock_env_variables
):
    """Test harvesting records from Zenodo API using legacy method."""
    # Mock the make_request method
    mock_zenodo_harvester.make_request = MagicMock()
    mock_zenodo_harvester.make_request.return_value = {
        "hits": {
            "hits": [sample_zenodo_record],
        },
        "links": {},
    }

    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_harvester.harvest_records(query=query))

    # Verify the expected calls and results
    mock_zenodo_harvester.make_request.assert_called_once()
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]
    assert records[0]["metadata"]["title"] == sample_zenodo_record["metadata"]["title"]


def test_harvest_records_with_query(mock_zenodo_harvester, sample_zenodo_record):
    """Test harvesting records with a specific query."""
    # Mock the make_request method
    mock_zenodo_harvester.make_request = MagicMock()
    mock_zenodo_harvester.make_request.return_value = {
        "hits": {"hits": [sample_zenodo_record]},
        "links": {},
    }

    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_harvester.harvest_records(query=query))

    # Get the parameters from the call
    args, kwargs = mock_zenodo_harvester.make_request.call_args
    assert kwargs["params"]["q"] == query

    # Verify the expected results
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]


def test_legacy_to_new_method(mock_zenodo_harvester):
    """Test that harvest_records calls get_records."""
    # Setup the mock
    mock_zenodo_harvester.get_records = MagicMock()
    mock_zenodo_harvester.get_records.return_value = [{"id": "test"}]

    # Call the legacy method
    list(mock_zenodo_harvester.harvest_records("test query"))

    # Verify it calls get_records
    mock_zenodo_harvester.get_records.assert_called_once_with(query="test query")
