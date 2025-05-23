"""Test custom exception classes for Invenio Migrator."""

from invenio_migrator.errors import (
    APIClientError,
    AuthenticationError,
    ConfigurationError,
    InvenioMigratorError,
    MigrationError,
    RecordMappingError,
    RecordValidationError,
)


class TestInvenioMigratorError:
    """Test the base InvenioMigratorError class."""

    def test_base_error(self):
        """Test creation of the base error."""
        error = InvenioMigratorError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_with_details(self):
        """Test creation with details."""
        error = InvenioMigratorError("Test error", "Additional details")
        assert str(error) == "Test error: Additional details"
        assert error.message == "Test error"
        assert error.details == "Additional details"


class TestAPIClientError:
    """Test APIClientError class."""

    def test_api_client_error(self):
        """Test creation of APIClientError."""
        error = APIClientError("API request failed", 500)
        assert error.status_code == 500
        assert "API request failed" in str(error)
        assert "Status: 500" in str(error)

    def test_with_response_data(self):
        """Test with response_data."""
        error = APIClientError(
            "API request failed", 404, {"error": "Resource not found"}
        )
        assert error.status_code == 404
        assert error.response_data == {"error": "Resource not found"}


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_authentication_error(self):
        """Test creation of AuthenticationError."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert "Authentication failed" in str(error)

    def test_custom_message(self):
        """Test with custom message."""
        error = AuthenticationError("Invalid token")
        assert error.status_code == 401
        assert "Invalid token" in str(error)


class TestRecordMappingError:
    """Test RecordMappingError class."""

    def test_basic_mapping_error(self):
        """Test basic mapping error."""
        error = RecordMappingError("record-1")
        assert "Failed to map record record-1" in str(error)
        assert error.record_id == "record-1"

    def test_with_field(self):
        """Test with field information."""
        error = RecordMappingError("record-1", field="creators")
        assert "Failed to map record record-1 (field: creators)" in str(error)
        assert error.field == "creators"

    def test_with_reason(self):
        """Test with reason."""
        error = RecordMappingError("record-1", field="date", reason="Invalid format")
        assert "Invalid format" in str(error)
        assert error.field == "date"
        assert error.record_id == "record-1"


class TestRecordValidationError:
    """Test RecordValidationError class."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = RecordValidationError("record-1")
        assert "Record validation failed for record-1" in str(error)
        assert error.record_id == "record-1"
        assert error.missing_fields == []
        assert error.invalid_fields == []

    def test_missing_fields(self):
        """Test with missing fields."""
        error = RecordValidationError("record-1", missing_fields=["title", "creator"])
        assert "Missing: title, creator" in str(error)

    def test_invalid_fields(self):
        """Test with invalid fields."""
        error = RecordValidationError("record-1", invalid_fields=["date"])
        assert "Invalid: date" in str(error)

    def test_missing_and_invalid(self):
        """Test with both missing and invalid fields."""
        error = RecordValidationError(
            "record-1", missing_fields=["title"], invalid_fields=["date"]
        )
        assert "Missing: title" in str(error)
        assert "Invalid: date" in str(error)


class TestMigrationError:
    """Test MigrationError class."""

    def test_migration_error(self):
        """Test migration error."""
        error = MigrationError("Migration failed")
        assert "Migration failed" in str(error)
        assert error.failed_records == []

    def test_with_failed_records(self):
        """Test with failed records."""
        failed = ["record-1", "record-2"]
        error = MigrationError("Migration failed", failed_records=failed)
        assert "Failed records: 2" in str(error)
        assert error.failed_records == failed


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_config_error(self):
        """Test configuration error."""
        error = ConfigurationError("API_TOKEN")
        assert "Configuration error for 'API_TOKEN'" in str(error)
        assert error.config_key == "API_TOKEN"

    def test_with_reason(self):
        """Test with reason."""
        error = ConfigurationError("API_URL", "URL must be HTTPS")
        assert "URL must be HTTPS" in str(error)
        assert error.config_key == "API_URL"
