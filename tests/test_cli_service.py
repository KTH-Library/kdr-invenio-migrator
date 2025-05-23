"""Test the CliService functionality."""

import json
from unittest.mock import MagicMock, patch

import pytest

from invenio_migrator.errors import InvenioMigratorError, MigrationError
from invenio_migrator.services.cli_service import CliService
from invenio_migrator.services.migration import MigrationService


@pytest.fixture
def mock_migration_service():
    """Create a mock migration service."""
    service = MagicMock(spec=MigrationService)
    return service


@pytest.fixture
def cli_service(mock_migration_service):
    """Create a CLI service with mocked migration service."""
    return CliService(migration_service=mock_migration_service)


@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary output file path."""
    return str(tmp_path / "output.json")


class TestCliService:
    """Test the CliService class."""

    def test_init_with_migration_service(self, mock_migration_service):
        """Test initialization with provided migration service."""
        service = CliService(migration_service=mock_migration_service)
        assert service.migration_service == mock_migration_service

    def test_init_without_migration_service(self):
        """Test initialization with default migration service."""
        with patch(
            "invenio_migrator.services.cli_service.MigrationService"
        ) as mock_migration_class:
            mock_service = MagicMock()
            mock_migration_class.return_value = mock_service

            service = CliService()

            # Verify MigrationService created
            mock_migration_class.assert_called_once()
            assert service.migration_service == mock_service

    def test_handle_migrate_command(self, cli_service, mock_migration_service):
        """Test basic migration command handling."""
        cli_service.handle_migrate_command(
            dry_run=True, query="test query", include_files=True
        )

        # Verify migration service called
        mock_migration_service.migrate_records.assert_called_once_with(
            dry_run=True, query="test query", include_files=True
        )

    def test_handle_migrate_command_with_output(
        self, cli_service, mock_migration_service, temp_output_file
    ):
        """Test migration command handling with output file."""
        # Setup mock provider and mapper
        mock_provider = MagicMock()
        mock_provider.get_records.return_value = [
            {"id": "record1", "metadata": {"title": "Record 1"}},
            {"id": "record2", "metadata": {"title": "Record 2"}},
        ]

        mock_mapper = MagicMock()
        mock_mapper.map_record.side_effect = [
            {"metadata": {"title": "Mapped Record 1"}, "files": {"enabled": False}},
            {"metadata": {"title": "Mapped Record 2"}, "files": {"enabled": False}},
        ]

        mock_migration_service.provider = mock_provider
        mock_migration_service.mapper = mock_mapper

        # Call with output file
        cli_service.handle_migrate_command(
            query="test query", output=temp_output_file, include_files=True
        )

        # Verify provider and mapper called
        mock_provider.get_records.assert_called_once_with(query="test query")
        assert mock_mapper.map_record.call_count == 2

        # Verify migration_service.migrate_records NOT called
        mock_migration_service.migrate_records.assert_not_called()

        # Verify file was created and contents
        from pathlib import Path

        assert Path(temp_output_file).exists()
        with Path(temp_output_file).open("r") as f:
            output_data = json.load(f)
            assert len(output_data) == 2
            assert output_data[0]["source_id"] == "record1"
            assert (
                output_data[0]["mapped_record"]["metadata"]["title"]
                == "Mapped Record 1"
            )
            assert (
                output_data[0]["mapped_record"]["files"]["enabled"] is True
            )  # Should be enabled

    def test_handle_migrate_command_with_mapping_error(
        self, cli_service, mock_migration_service, temp_output_file
    ):
        """Test migration with mapping errors when saving to file."""
        # Setup mock provider and mapper
        mock_provider = MagicMock()
        mock_provider.get_records.return_value = [
            {"id": "record1", "metadata": {"title": "Record 1"}},
            {"id": "record2", "metadata": {"title": "Record 2"}},
        ]

        mock_mapper = MagicMock()
        mock_mapper.map_record.side_effect = [
            {"metadata": {"title": "Mapped Record 1"}},
            Exception("Mapping error for record2"),
        ]

        mock_migration_service.provider = mock_provider
        mock_migration_service.mapper = mock_mapper

        # Call with output file
        cli_service.handle_migrate_command(query="test query", output=temp_output_file)
        # Verify file contains the error information
        from pathlib import Path

        with Path(temp_output_file).open("r") as f:
            output_data = json.load(f)
            assert len(output_data) == 2
            assert "mapped_record" in output_data[0]
            assert "mapping_error" in output_data[1]
            assert "Mapping error for record2" in output_data[1]["mapping_error"]
            assert "Mapping error for record2" in output_data[1]["mapping_error"]

    def test_handle_migrate_command_migration_error(
        self, cli_service, mock_migration_service
    ):
        """Test handling of migration errors."""
        failed_records = [{"id": "record1", "error": "Failed to map"}]
        mock_migration_service.migrate_records.side_effect = MigrationError(
            "Migration failed", failed_records=failed_records
        )

        with pytest.raises(MigrationError) as exc_info:
            cli_service.handle_migrate_command()

        assert "Migration failed" in str(exc_info.value)
        assert exc_info.value.failed_records == failed_records

    def test_handle_migrate_command_http_error(
        self, cli_service, mock_migration_service
    ):
        """Test handling of HTTP errors."""
        from requests.exceptions import HTTPError

        http_error = HTTPError("HTTP Error")
        mock_migration_service.migrate_records.side_effect = http_error

        with pytest.raises(InvenioMigratorError) as exc_info:
            cli_service.handle_migrate_command()

        assert "Network error" in str(exc_info.value)
        assert "HTTP Error" in exc_info.value.details

    def test_handle_migrate_command_unexpected_error(
        self, cli_service, mock_migration_service
    ):
        """Test handling of unexpected errors."""
        error = ValueError("Unexpected error")
        mock_migration_service.migrate_records.side_effect = error

        with pytest.raises(InvenioMigratorError) as exc_info:
            cli_service.handle_migrate_command()

        assert "Unexpected migration error" in str(exc_info.value)
        assert "Unexpected error" in exc_info.value.details

    def test_handle_output_to_file_error(
        self, cli_service, mock_migration_service, tmp_path
    ):
        """Test error handling when saving to file fails."""
        invalid_path = str(tmp_path / "nonexistent_dir" / "output.json")

        # Setup mock provider to prevent 'Mock has no attribute provider' error
        mock_provider = MagicMock()
        mock_provider.get_records.return_value = [{"id": "record1"}]
        mock_migration_service.provider = mock_provider
        
        # Configure mapper to return a simple record
        mock_mapper = MagicMock()
        mock_mapper.map_record.return_value = {"metadata": {"title": "Test Record"}}
        mock_migration_service.mapper = mock_mapper

        # Create a custom permission error with a clear message
        permission_error = PermissionError("Permission denied for test file")
        
        # Setup to make the file write operation fail
        with patch("pathlib.Path.open", side_effect=permission_error):
            with pytest.raises(InvenioMigratorError) as exc_info:
                cli_service.handle_migrate_command(output=invalid_path)

            # Check the exception details
            error_message = str(exc_info.value)
            error_details = exc_info.value.details
            
            # Verify proper error handling
            assert "Failed to save records to file" in error_message
            assert "Permission denied for test file" in error_details
