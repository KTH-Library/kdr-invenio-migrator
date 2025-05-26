"""Test the InvenioRDMClient functionality."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from invenio_migrator.clients.target import (
    InvenioRDMClient,
)  # Removed TargetClient import
from invenio_migrator.errors import APIClientError, AuthenticationError


@pytest.fixture
def mock_config():
    """Mock the CONFIG dictionary."""
    return {
        "TARGET_BASE_URL": "https://invenio.example.org/api",
        "TARGET_API_TOKEN": "test-token",
        "SESSION": {"VERIFY_SSL": False},
        "RATE_LIMITS": {
            "REQUEST_DELAY_SECONDS": 0.1,  # Short delay for testing
            "MAX_RETRIES": 3,
        },
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
            assert client.request_delay == 0.1
            assert client.request_max_retries == 3

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


class TestRetryMechanism:
    """Test the retry mechanism and rate limiting functionality."""

    @pytest.fixture
    def mock_func(self):
        """Create a mock function for testing retry mechanism."""
        return MagicMock()

    def test_retry_with_backoff_success_first_attempt(self, invenio_client, mock_func):
        """Test successful execution on first attempt."""
        mock_func.return_value = "success"

        result = invenio_client._retry_with_backoff(
            mock_func, "arg1", "arg2", kwarg1="value1"
        )

        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1")

    def test_retry_with_backoff_429_status_code(self, invenio_client, mock_func):
        """Test retry mechanism with 429 status code error."""
        # Create a mock exception with 429 status code
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = requests.HTTPError("429 Client Error")
        error.response = mock_response

        # First two calls fail with 429, third succeeds
        mock_func.side_effect = [error, error, "success"]

        with patch("time.sleep") as mock_sleep:
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

        # Verify exponential backoff timing
        expected_waits = [0.1, 0.2]  # 2^0 * 0.1, 2^1 * 0.1
        actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_calls == expected_waits

    def test_retry_with_backoff_429_in_string(self, invenio_client, mock_func):
        """Test retry mechanism with '429' in error string."""
        error = Exception("429 Client Error: TOO MANY REQUESTS")

        # First two calls fail, third succeeds
        mock_func.side_effect = [error, error, "success"]

        with patch("time.sleep") as mock_sleep:
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retry_with_backoff_too_many_requests_in_string(
        self, invenio_client, mock_func
    ):
        """Test retry mechanism with 'TOO MANY REQUESTS' in error string."""
        error = Exception("TOO MANY REQUESTS for url: https://example.com/api")

        # First call fails, second succeeds
        mock_func.side_effect = [error, "success"]

        with patch("time.sleep") as mock_sleep:
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1

    def test_retry_with_backoff_max_retries_exceeded(self, invenio_client, mock_func):
        """Test retry mechanism when max retries are exceeded."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = requests.HTTPError("429 Client Error")
        error.response = mock_response

        # All calls fail with 429
        mock_func.side_effect = error

        with patch("time.sleep"):
            with pytest.raises(APIClientError) as exc_info:
                invenio_client._retry_with_backoff(mock_func)

        assert "Rate limit exceeded after 3 retries" in str(exc_info.value)
        assert mock_func.call_count == 4  # Initial + 3 retries

    def test_retry_with_backoff_custom_max_retries(self, invenio_client, mock_func):
        """Test retry mechanism with custom max retries."""
        error = Exception("429 Client Error")
        mock_func.side_effect = error

        with patch("time.sleep"):
            with pytest.raises(APIClientError) as exc_info:
                invenio_client._retry_with_backoff(mock_func, max_retries=1)

        assert "Rate limit exceeded after 1 retries" in str(exc_info.value)
        assert mock_func.call_count == 2  # Initial + 1 retry

    def test_retry_with_backoff_non_rate_limit_error(self, invenio_client, mock_func):
        """Test that non-rate-limit errors are raised immediately."""
        error = ValueError("Invalid data")
        mock_func.side_effect = error

        with pytest.raises(ValueError) as exc_info:
            invenio_client._retry_with_backoff(mock_func)

        assert "Invalid data" in str(exc_info.value)
        assert mock_func.call_count == 1  # No retries for non-rate-limit errors

    def test_retry_with_backoff_exponential_timing(self, invenio_client, mock_func):
        """Test that retry timing follows exponential backoff pattern."""
        error = Exception("429 TOO MANY REQUESTS")
        mock_func.side_effect = [error, error, error, "success"]

        with patch("time.sleep") as mock_sleep:
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"

        # Verify exponential backoff: 2^0 * 0.1, 2^1 * 0.1, 2^2 * 0.1
        expected_waits = [0.1, 0.2, 0.4]
        actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_calls == expected_waits

    def test_create_record_with_retry(self, invenio_client):
        """Test create_record method using retry mechanism."""
        # Mock 429 error followed by success
        mock_response_success = MagicMock()
        mock_response_success.data._data = {"id": "record1", "metadata": {}}

        mock_response_error = MagicMock()
        mock_response_error.status_code = 429
        error = requests.HTTPError("429 Client Error")
        error.response = mock_response_error

        invenio_client.records.create.side_effect = [error, mock_response_success]

        record_data = {
            "metadata": {"title": "Test Title"},
            "access": {"record": "public", "files": "public"},
        }

        with patch("time.sleep"):
            result = invenio_client.create_record(record_data)

        assert result["id"] == "record1"
        assert invenio_client.records.create.call_count == 2

    def test_create_record_api_errors_in_response(self, invenio_client):
        """Test create_record handling API errors in response data."""
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "record1",
            "errors": [
                {
                    "field": "pids.doi",
                    "messages": ["doi:10.5281/zenodo.15411009 already exists."],
                }
            ],
        }
        invenio_client.records.create.return_value = mock_response

        record_data = {
            "metadata": {"title": "Test Title"},
            "access": {"record": "public", "files": "public"},
        }

        with pytest.raises(APIClientError) as exc_info:
            invenio_client.create_record(record_data)

        assert "Failed to draft creation" in str(exc_info.value)
        assert "pids.doi: doi:10.5281/zenodo.15411009 already exists." in str(
            exc_info.value
        )

    def test_create_review_request_with_rate_limiting(self, invenio_client):
        """Test create_review_request applies rate limiting."""
        mock_resource = MagicMock()
        mock_response = MagicMock()
        mock_response.data._data = {
            "id": "request1",
            "links": {"self": "https://example.org/requests/1"},
        }
        mock_resource.create.return_value = mock_response

        with patch(
            "invenio_migrator.clients.target.CommunitySubmissionResource",
            return_value=mock_resource,
        ):
            with patch("time.sleep") as mock_sleep:
                result = invenio_client.create_review_request("draft1", "community1")

        assert result["id"] == "request1"
        # Verify rate limiting delay was applied
        mock_sleep.assert_called_once_with(0.1)

    def test_check_api_errors_with_multiple_errors(self, invenio_client):
        """Test _check_api_errors with multiple field errors."""
        response_data = {
            "id": "record1",
            "errors": [
                {
                    "field": "metadata.title",
                    "messages": ["Title is required", "Title too short"],
                },
                {"field": "pids.doi", "messages": ["DOI already exists"]},
            ],
        }

        with pytest.raises(APIClientError) as exc_info:
            invenio_client._check_api_errors(response_data, "Test operation")

        error_msg = str(exc_info.value)
        assert "Failed to test operation" in error_msg
        assert "metadata.title: Title is required" in error_msg
        assert "metadata.title: Title too short" in error_msg
        assert "pids.doi: DOI already exists" in error_msg

    def test_check_api_errors_no_errors(self, invenio_client):
        """Test _check_api_errors with no errors in response."""
        response_data = {"id": "record1", "metadata": {}}

        # Should not raise any exception
        invenio_client._check_api_errors(response_data, "Test operation")

    def test_check_api_errors_empty_errors_list(self, invenio_client):
        """Test _check_api_errors with empty errors list."""
        response_data = {"id": "record1", "errors": []}

        # Should not raise any exception
        invenio_client._check_api_errors(response_data, "Test operation")

    def test_retry_with_mixed_error_types(self, invenio_client, mock_func):
        """Test retry mechanism with different types of 429 errors."""
        # Mix of different 429 error formats
        mock_response = MagicMock()
        mock_response.status_code = 429
        http_error = requests.HTTPError("429 Client Error")
        http_error.response = mock_response

        string_error = Exception("TOO MANY REQUESTS for url")

        mock_func.side_effect = [http_error, string_error, "success"]

        with patch("time.sleep") as mock_sleep:
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("invenio_migrator.clients.target.logger")
    def test_retry_logging(self, mock_logger, invenio_client, mock_func):
        """Test that retry attempts are properly logged."""
        error = Exception("429 TOO MANY REQUESTS")
        mock_func.side_effect = [error, error, "success"]

        with patch("time.sleep"):
            result = invenio_client._retry_with_backoff(mock_func)

        assert result == "success"

        # Check warning logs for retry attempts
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) == 2

        # Verify log messages contain retry information
        for i, call in enumerate(warning_calls):
            log_msg = call[0][0]
            assert "Rate limited (429), retrying in" in log_msg
            assert f"attempt {i + 1}/4" in log_msg

    @patch("invenio_migrator.clients.target.logger")
    def test_retry_max_retries_logging(self, mock_logger, invenio_client, mock_func):
        """Test logging when max retries are exceeded."""
        error = Exception("429 TOO MANY REQUESTS")
        mock_func.side_effect = error

        with patch("time.sleep"):
            with pytest.raises(APIClientError):
                invenio_client._retry_with_backoff(mock_func)

        # Check error log for max retries exceeded
        mock_logger.error.assert_called_with("Rate limited after 3 retries, giving up")
