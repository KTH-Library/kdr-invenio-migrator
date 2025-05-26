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
def temp_output_file(tests_tmp_path):
    """Create a temporary output file path."""
    return str(tests_tmp_path / "output.json")


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
            dry_run=True, query="test query", include_files=True, record_or_records=None
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
        mock_provider.get_records.assert_called_once_with(
            query="test query", record_or_records=None
        )
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
        self, cli_service, mock_migration_service, tests_tmp_path
    ):
        """Test error handling when outputting to a file."""
        # Setup mock migration service to return some data
        # This is not strictly needed anymore as the provider/mapper path is taken
        # mock_migration_service.migrate_records.return_value = [
        #     {"id": "record1", "metadata": {"title": "Record 1"}}
        # ]
        # Setup mock provider and mapper for the case when output is to a file
        mock_provider = MagicMock()
        mock_provider.get_records.return_value = [
            {"id": "record1", "metadata": {"title": "Record 1"}},
        ]
        mock_mapper = MagicMock()
        mock_mapper.map_record.return_value = {
            "metadata": {"title": "Mapped Record 1"},
            "files": {"enabled": False},
        }
        mock_migration_service.provider = mock_provider
        mock_migration_service.mapper = mock_mapper

        # Create a directory where a file is expected to test permission error
        # (This is a simplified way to simulate a write error; specific OS/filesystem behavior might vary)
        error_path = tests_tmp_path / "protected_dir"
        error_path.mkdir()
        # Attempt to make it read-only to cause a write error - this might not work on all systems
        # or might not prevent writing depending on user privileges.
        # A more robust test might involve mocking `open` or `json.dump`.
        try:
            error_path.chmod(0o400)  # Replaced os.chmod with Path.chmod
        except PermissionError:
            # If we can't change permissions (e.g. not owner), this part of the test might not be effective
            pass

        output_file_in_protected_dir = error_path / "output.jsonl"

        # Temporarily mock open to simulate a permission error more reliably
        with patch(
            "builtins.open", side_effect=PermissionError("Simulated permission denied")
        ):
            with pytest.raises(InvenioMigratorError) as exc_info:
                cli_service.handle_migrate_command(
                    dry_run=True,  # dry_run is True, so migrate_records won't be called
                    query="test query",
                    output=str(output_file_in_protected_dir),
                    include_files=False,
                )
        assert "Failed to save records to file" in str(
            exc_info.value
        )  # Changed assertion
        # Clean up the read-only permission to allow the directory to be removed
        try:
            error_path.chmod(0o700)
        except PermissionError:
            pass
