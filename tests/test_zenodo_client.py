"""Test the ZenodoClient functionality."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from invenio_migrator.clients.zenodo import ZenodoClient
from invenio_migrator.errors import APIClientError, AuthenticationError


@pytest.fixture
def mock_config():
    """Mock the CONFIG dictionary."""
    return {
        "SOURCE_BASE_URL": "https://zenodo.example.org/api",
        "SOURCE_API_TOKEN": "test-token",
        "SOURCE_COMMUNITY_ID": "test-community",
        "RATE_LIMITS": {"SOURCE_REQUEST_DELAY_SECONDS": 0},
    }


@pytest.fixture
def zenodo_client(mock_config):
    """Create a ZenodoClient with mocked config and session."""
    with patch("invenio_migrator.clients.zenodo.CONFIG", mock_config):
        client = ZenodoClient()
        client._session = MagicMock()
        return client


class TestZenodoClient:
    """Test the ZenodoClient class."""

    def test_init(self, mock_config):
        """Test initialization with config values."""
        with patch("invenio_migrator.clients.zenodo.CONFIG", mock_config):
            client = ZenodoClient()
            assert client.base_url == "https://zenodo.example.org/api"
            assert client.api_token == "test-token"
            assert client.community_id == "test-community"
            assert client.request_delay == 0

    def test_make_request_success(self, zenodo_client):
        """Test successful API request."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}
        zenodo_client._session.get.return_value = mock_response

        result = zenodo_client.make_request("https://example.org/test")
        assert result == {"test": "data"}
        zenodo_client._session.get.assert_called_once_with("https://example.org/test")

    def test_make_request_auth_error(self, zenodo_client):
        """Test authentication error handling."""
        # Mock an authentication error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 401
        mock_response.content = b'{"error": "Unauthorized"}'
        mock_response.json.return_value = {"error": "Unauthorized"}

        error_obj = requests.exceptions.HTTPError()
        error_obj.response = mock_response
        zenodo_client._session.get.side_effect = error_obj

        with pytest.raises(AuthenticationError):
            zenodo_client.make_request("https://example.org/test")

    def test_make_request_http_error(self, zenodo_client):
        """Test HTTP error handling."""
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 500
        mock_response.content = b'{"error": "Server error"}'
        mock_response.json.return_value = {"error": "Server error"}

        error_obj = requests.exceptions.HTTPError()
        error_obj.response = mock_response
        zenodo_client._session.get.side_effect = error_obj

        with pytest.raises(APIClientError) as exc_info:
            zenodo_client.make_request("https://example.org/test")

        assert exc_info.value.status_code == 500
        assert exc_info.value.response_data == {"error": "Server error"}

    def test_make_request_connection_error(self, zenodo_client):
        """Test connection error handling."""
        zenodo_client._session.get.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with pytest.raises(APIClientError) as exc_info:
            zenodo_client.make_request("https://example.org/test")

        assert "Connection failed" in str(exc_info.value)

    def test_get_records(self, zenodo_client):
        """Test retrieving records with pagination."""
        # Mock first page response
        first_page = {
            "hits": {"hits": [{"id": "record1"}, {"id": "record2"}]},
            "links": {"next": "https://zenodo.example.org/api/records?page=2"},
        }

        # Mock second (last) page response
        last_page = {"hits": {"hits": [{"id": "record3"}]}, "links": {}}

        # Setup the sequence of responses
        zenodo_client.make_request = MagicMock(side_effect=[first_page, last_page])

        # Get all records
        records = list(zenodo_client.get_records("test query"))

        # Verify we got all records from both pages
        assert len(records) == 3
        assert records[0]["id"] == "record1"
        assert records[1]["id"] == "record2"
        assert records[2]["id"] == "record3"

        # Verify the API calls
        assert zenodo_client.make_request.call_count == 2

        # Check first call had the correct parameters
        args, kwargs = zenodo_client.make_request.call_args_list[0]
        assert args[0] == "https://zenodo.example.org/api/records"
        assert kwargs["params"]["q"] == "test query"
        assert kwargs["params"]["communities"] == "test-community"

        # Second call should use the next URL without params
        args, kwargs = zenodo_client.make_request.call_args_list[1]
        assert args[0] == "https://zenodo.example.org/api/records?page=2"
        assert "params" not in kwargs or kwargs["params"] is None

    def test_get_record(self, zenodo_client):
        """Test retrieving a single record."""
        # Mock the response
        zenodo_client.make_request = MagicMock(
            return_value={"id": "record1", "metadata": {}}
        )

        # Get the record
        record = zenodo_client.get_record("record1")

        # Verify the result
        assert record["id"] == "record1"

        # Verify the API call
        zenodo_client.make_request.assert_called_once_with(
            "https://zenodo.example.org/api/records/record1"
        )

    def test_get_record_not_found(self, zenodo_client):
        """Test handling of record not found."""
        # Mock a 404 error
        error = APIClientError("Not found", status_code=404)
        zenodo_client.make_request = MagicMock(side_effect=error)

        # The method should return None
        assert zenodo_client.get_record("nonexistent") is None

    def test_get_record_other_error(self, zenodo_client):
        """Test handling of other errors when getting a record."""
        # Mock a 500 error
        error = APIClientError("Server error", status_code=500)
        zenodo_client.make_request = MagicMock(side_effect=error)

        # The method should propagate the error
        with pytest.raises(APIClientError):
            zenodo_client.get_record("record1")

    def test_backward_compatibility(self, zenodo_client):
        """Test the backward compatibility method."""
        # Setup the mock
        zenodo_client.get_records = MagicMock(return_value=[{"id": "record1"}])

        # Call the legacy method
        list(zenodo_client.harvest_records("test query"))

        # Verify it calls get_records
        zenodo_client.get_records.assert_called_once_with(query="test query")

    def test_get_record_count(self, zenodo_client):
        """Test retrieving record count."""
        # Mock the response
        mock_response = {"hits": {"total": 42}}
        zenodo_client.make_request = MagicMock(return_value=mock_response)

        # Get the record count
        count = zenodo_client.get_record_count("test query")

        # Verify the result
        assert count == 42

        # Verify the API call
        args, kwargs = zenodo_client.make_request.call_args
        assert args[0] == "https://zenodo.example.org/api/records"
        assert kwargs["params"]["q"] == "test query"
        assert kwargs["params"]["communities"] == "test-community"
        assert kwargs["params"]["size"] == 1

    def test_get_record_count_error(self, zenodo_client):
        """Test error handling in get_record_count."""
        # Mock an API error
        zenodo_client.make_request = MagicMock(side_effect=APIClientError("API error"))

        # Should return 0 on error
        assert zenodo_client.get_record_count("test query") == 0

    def test_validate_connection_success(self, zenodo_client):
        """Test successful connection validation."""
        # Mock successful response
        zenodo_client.make_request = MagicMock(return_value={"hits": {"total": 1}})

        # Should return True for successful connection
        assert zenodo_client.validate_connection() is True

        # Verify the API call
        args, kwargs = zenodo_client.make_request.call_args
        assert args[0] == "https://zenodo.example.org/api/records"
        assert kwargs["params"]["size"] == 1

    def test_validate_connection_failure(self, zenodo_client):
        """Test failed connection validation."""
        # Mock a connection error
        zenodo_client.make_request = MagicMock(
            side_effect=Exception("Connection failed")
        )

        # Should return False for failed connection
        assert zenodo_client.validate_connection() is False
