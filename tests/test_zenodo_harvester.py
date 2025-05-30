"""Test the Zenodo harvester functionality (for legacy code compatibility)."""

from unittest.mock import MagicMock, patch

import pytest

from invenio_migrator.clients.zenodo import ZenodoClient


@pytest.fixture
def mock_zenodo_client():
    """Fixture to provide a mocked ZenodoClient."""
    with patch(
        "invenio_migrator.clients.zenodo.CONFIG",
        {
            "SOURCE_BASE_URL": "https://zenodo.example.org/api",
            "SOURCE_API_TOKEN": "test-token",
            "SOURCE_COMMUNITY_ID": "test-community",
            "RATE_LIMITS": {"SOURCE_REQUEST_DELAY_SECONDS": 0},
            "SESSION": {"VERIFY_SSL": False, "TIMEOUT": 30},
        },
    ):
        client = ZenodoClient()
        client._session = MagicMock()
        return client


def test_get_records(mock_zenodo_client, sample_zenodo_record, mock_env_variables):
    """Test harvesting records from Zenodo API."""
    # Mock the make_request method
    mock_zenodo_client.make_request = MagicMock()
    mock_zenodo_client.make_request.return_value = {
        "hits": {
            "hits": [sample_zenodo_record],
        },
        "links": {},
    }

    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_client.get_records(query=query))

    # Verify the expected calls and results
    mock_zenodo_client.make_request.assert_called_once()
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]
    assert records[0]["metadata"]["title"] == sample_zenodo_record["metadata"]["title"]


def test_get_records_with_query(mock_zenodo_client, sample_zenodo_record):
    """Test harvesting records with a specific query."""
    # Mock the make_request method
    mock_zenodo_client.make_request = MagicMock()
    mock_zenodo_client.make_request.return_value = {
        "hits": {"hits": [sample_zenodo_record]},
        "links": {},
    }

    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_client.get_records(query=query))

    # Get the parameters from the call
    args, kwargs = mock_zenodo_client.make_request.call_args
    assert kwargs["params"]["q"] == query

    # Verify the expected results
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]
