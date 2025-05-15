"""Test the Zenodo harvester functionality."""
from unittest.mock import MagicMock

import pytest

from invenio_migrator.clients.zenodo import ZenodoHarvester


@pytest.fixture
def mock_zenodo_harvester():
    """Fixture to provide a mocked ZenodoHarvester."""
    harvester = ZenodoHarvester()
    harvester._request_session = MagicMock()
    return harvester


def test_harvest_records(mock_zenodo_harvester, sample_zenodo_record, mock_env_variables):
    """Test harvesting records from Zenodo API."""
    # Mock the _make_request method
    mock_zenodo_harvester._make_request = MagicMock()
    mock_zenodo_harvester._make_request.return_value = {
        "hits": {
            "hits": [sample_zenodo_record],
        },
        "links": {}
    }
    
    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_harvester.harvest_records(query=query))
    
    # Verify the expected calls and results
    mock_zenodo_harvester._make_request.assert_called_once()
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]
    assert records[0]["metadata"]["title"] == sample_zenodo_record["metadata"]["title"]


def test_harvest_records_with_query(mock_zenodo_harvester, sample_zenodo_record):
    """Test harvesting records with a specific query."""
    # Mock the _make_request method
    mock_zenodo_harvester._make_request = MagicMock()
    mock_zenodo_harvester._make_request.return_value = {
        "hits": {
            "hits": [sample_zenodo_record]
        },
        "links": {}
    }
    
    # Call the harvest_records method with a query
    query = "metadata.publication_date:{2025-01-01 TO *}"
    records = list(mock_zenodo_harvester.harvest_records(query=query))
    
    # Verify the query was used in the URL
    args, _ = mock_zenodo_harvester._make_request.call_args
    assert query in args[0]
    
    # Verify the expected results
    assert len(records) == 1
    assert records[0]["doi"] == sample_zenodo_record["doi"]
