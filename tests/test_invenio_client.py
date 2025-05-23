"""Test the InvenioRDMClient functionality."""

from unittest.mock import MagicMock, patch

import pytest

from invenio_migrator.clients.target import (
    InvenioRDMClient,  # Removed TargetClient import
)
from invenio_migrator.errors import APIClientError, AuthenticationError


@pytest.fixture
def mock_config():
    """Mock the CONFIG dictionary."""
    return {
        "TARGET_BASE_URL": "https://invenio.example.org/api",
        "TARGET_API_TOKEN": "test-token",
        "SESSION": {"VERIFY_SSL": False},
    }


@pytest.fixture
def invenio_client(mock_config):
    """Create an InvenioRDMClient with mocked config and client."""
    with patch("invenio_migrator.clients.target.CONFIG", mock_config):
        with patch("invenio_migrator.clients.target.InvenioAPI") as mock_invenio_api:
            # Setup mock InvenioAPI
            mock_api = MagicMock()
            mock_invenio_api.return_value = mock_api

            client = InvenioRDMClient()

            # Verify the client was set up correctly
            assert client.client == mock_api

            return client


class TestInvenioRDMClient:
    """Test the InvenioRDMClient class."""

    def test_init(self, mock_config):
        """Test initialization with config values."""
        with (
            patch("invenio_migrator.clients.target.CONFIG", mock_config),
            patch("invenio_migrator.clients.target.InvenioAPI"),
        ):
            client = InvenioRDMClient()
            assert client.base_url == "https://invenio.example.org/api"
            assert client.api_token == "test-token"

    def test_init_no_token(self, mock_config):
        """Test initialization with missing API token."""
        mock_config["TARGET_API_TOKEN"] = None

        with (
            patch("invenio_migrator.clients.target.CONFIG", mock_config),
            patch("invenio_migrator.clients.target.Session"),
        ):
            with pytest.raises(AuthenticationError) as exc_info:
                InvenioRDMClient()

            assert "TARGET_API_TOKEN is required" in str(exc_info.value)

    def test_create_record(self, invenio_client):
        """Test creating a record."""
        # Mock the records.create method
        mock_response = MagicMock()
        mock_response.data._data = {"id": "record1", "metadata": {}}
        invenio_client.records.create.return_value = mock_response

        # Create a record
        record_data = {
            "metadata": {"title": "Test Title"},
            "access": {"record": "public", "files": "public"},
        }
        result = invenio_client.create_record(record_data)

        # Verify the result
        assert result["id"] == "record1"

        # Verify the API call
        invenio_client.records.create.assert_called_once()
        args, kwargs = invenio_client.records.create.call_args
        assert kwargs["data"]._data == record_data

    def test_create_record_error(self, invenio_client):
        """Test error handling when creating a record."""
        # Mock an error
        invenio_client.records.create.side_effect = Exception("API error")

        # Try to create a record
        record_data = {
            "metadata": {"title": "Test Title"},
            "access": {"record": "public", "files": "public"},
        }

        # The method should raise APIClientError
        with pytest.raises(APIClientError) as exc_info:
            invenio_client.create_record(record_data)

        assert "Failed to create record" in str(exc_info.value)
        assert "API error" in str(exc_info.value)

    def test_update_record(self, invenio_client):
        """Test update record (currently not implemented)."""
        # This test is no longer relevant as update_record is removed
        pass

    def test_delete_record(self, invenio_client):
        """Test delete record (currently not implemented)."""
        # This test is no longer relevant as delete_record is removed
        pass

    def test_create_review_request(self, invenio_client):
        """Test creating a review request."""
        # Mock the response
        mock_resource = MagicMock()
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "request1",
            "links": {"self": "https://example.org/requests/1"},
        }
        mock_resource.create.return_value = mock_response

        # Mock the resource class
        with patch(
            "invenio_migrator.clients.target.CommunitySubmissionResource",
            return_value=mock_resource,
        ):
            result = invenio_client.create_review_request("draft1", "community1")

            # Verify the result
            assert result["id"] == "request1"
            assert result["links"]["self"] == "https://example.org/requests/1"

            # Verify the resource instantiation
            from invenio_migrator.clients.target import CommunitySubmissionResource

            CommunitySubmissionResource.assert_called_once_with(
                invenio_client.client, id_="draft1"
            )

            # Verify the create call
            mock_resource.create.assert_called_once()

    def test_submit_review(self, invenio_client):
        """Test submitting a review."""
        # Mock the response
        mock_resource = MagicMock()
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "review1",
            "links": {"self": "https://example.org/reviews/1"},
        }
        mock_resource.submit.return_value = mock_response

        # Mock the resource class
        with patch(
            "invenio_migrator.clients.target.SubmitReviewResource",
            return_value=mock_resource,
        ):
            result = invenio_client.submit_review("draft1", "This looks good!")

            # Verify the result
            assert result["id"] == "review1"
            assert result["links"]["self"] == "https://example.org/reviews/1"

            # Verify the resource instantiation
            from invenio_migrator.clients.target import SubmitReviewResource

            SubmitReviewResource.assert_called_once_with(
                invenio_client.client, id_="draft1"
            )

            # Verify the submit call
            mock_resource.submit.assert_called_once()

    def test_accept_request(self, invenio_client):
        """Test accepting a request."""
        # Mock the response
        mock_resource = MagicMock()
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "acceptance1",
            "links": {"self": "https://example.org/acceptances/1"},
        }
        mock_resource.accept.return_value = mock_response

        # Mock the resource class
        with patch(
            "invenio_migrator.clients.target.RequestActionsResource",
            return_value=mock_resource,
        ):
            result = invenio_client.accept_request("request1", "Accepted!")

            # Verify the result
            assert result["id"] == "acceptance1"
            assert result["links"]["self"] == "https://example.org/acceptances/1"

            # Verify the resource instantiation
            from invenio_migrator.clients.target import RequestActionsResource

            RequestActionsResource.assert_called_once_with(
                invenio_client.client, request_id="request1"
            )

            # Verify the accept call
            mock_resource.accept.assert_called_once()

    def test_backward_compatibility(self, invenio_client):
        """Test backward compatibility with TargetClient."""
        # This test is no longer relevant as TargetClient is removed
        pass

    def test_get_record(self, invenio_client):
        """Test getting a record by ID."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "record1",
            "metadata": {"title": "Test Title"},
        }
        invenio_client.records.get.return_value = mock_response

        # Get the record
        result = invenio_client.get_record("record1")

        # Verify the result
        assert result["id"] == "record1"
        assert result["metadata"]["title"] == "Test Title"

        # Verify the API call
        invenio_client.records.get.assert_called_once_with(id_="record1")

    def test_get_record_error(self, invenio_client):
        """Test error handling when getting a record."""
        # Mock an error
        invenio_client.records.get.side_effect = Exception("API error")

        # Try to get a non-existent record
        result = invenio_client.get_record("nonexistent")

        # Should return None on error
        assert result is None

    def test_validate_connection_success(self, invenio_client):
        """Test successful connection validation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        invenio_client.client.get.return_value = mock_response

        # Should return True for successful connection
        assert invenio_client.validate_connection() is True

        # Verify API call
        invenio_client.client.get.assert_called_once_with(f"{invenio_client.base_url}/")

    def test_validate_connection_failure(self, invenio_client):
        """Test failed connection validation."""
        # Mock a failed response
        invenio_client.client.get.side_effect = Exception("Connection failed")

        # Should return False for failed connection
        assert invenio_client.validate_connection() is False
