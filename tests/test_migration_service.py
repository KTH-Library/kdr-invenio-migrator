"""Test the MigrationService functionality."""

from unittest.mock import MagicMock, patch

import pytest

from invenio_migrator.clients.target import InvenioRDMClient
from invenio_migrator.errors import MigrationError, RecordMappingError
from invenio_migrator.services.migration import MigrationService, RecordMapper


@pytest.fixture
def mock_provider():
    """Fixture to create a mock RecordProviderInterface."""
    provider = MagicMock()
    provider.get_records.return_value = [
        {"id": "record1", "metadata": {"title": "Record 1"}},
        {"id": "record2", "metadata": {"title": "Record 2"}},
    ]
    provider.get_record.return_value = {
        "id": "record1",
        "metadata": {"title": "Record 1"},
    }
    return provider


@pytest.fixture
def mock_consumer():
    """Fixture to create a mock RecordConsumerInterface."""
    consumer = MagicMock(spec=InvenioRDMClient)
    consumer.create_record.return_value = {
        "id": "draft-1",
        "metadata": {"title": "Record 1"},
    }
    return consumer


@pytest.fixture
def mock_mapper():
    """Fixture to create a mock RecordMapperInterface."""
    mapper = MagicMock()
    mapper.map_record.return_value = {
        "access": {"record": "public", "files": "public"},
        "files": {"enabled": True},
        "metadata": {"title": "Mapped Record"},
        "pids": {"doi": {"identifier": "10.1234/test", "provider": "external"}},
    }
    mapper.validate_mapped_record.return_value = True
    return mapper


@pytest.fixture
def migration_service(mock_provider, mock_consumer, mock_mapper):
    """Fixture to create a MigrationService with mocked dependencies."""
    return MigrationService(
        provider=mock_provider, consumer=mock_consumer, mapper=mock_mapper
    )


@pytest.fixture
def mock_config():
    """Mock the CONFIG dictionary."""
    return {
        "MIGRATION_OPTIONS": {"STOP_ON_ERROR": False},
        "INVENIORDM_COMMUNITY_ID": "test-community",
        "COMMUNITY_REVIEW_CONTENT": "Test review content",
    }


class TestMigrationService:
    """Test the MigrationService class."""

    def test_init_with_dependencies(self, mock_provider, mock_consumer, mock_mapper):
        """Test initialization with provided dependencies."""
        service = MigrationService(
            provider=mock_provider, consumer=mock_consumer, mapper=mock_mapper
        )

        assert service.provider == mock_provider
        assert service.consumer == mock_consumer
        assert service.mapper == mock_mapper

    def test_init_without_dependencies(self):
        """Test initialization with default dependencies."""
        with (
            patch("invenio_migrator.services.migration.ZenodoClient") as mock_zenodo,
            patch(
                "invenio_migrator.services.migration.InvenioRDMClient"
            ) as mock_invenio,
            patch(
                "invenio_migrator.services.migration.ZenodoToInvenioRDMMapper"
            ) as mock_mapper_class,
        ):
            mock_zenodo_instance = MagicMock()
            mock_invenio_instance = MagicMock()
            mock_mapper_instance = MagicMock()

            mock_zenodo.return_value = mock_zenodo_instance
            mock_invenio.return_value = mock_invenio_instance
            mock_mapper_class.return_value = mock_mapper_instance

            service = MigrationService()

            assert service.provider == mock_zenodo_instance
            assert service.consumer == mock_invenio_instance
            assert service.mapper == mock_mapper_instance

    def test_migrate_records_success(
        self, migration_service, mock_provider, mock_consumer, mock_mapper, mock_config
    ):
        """Test successful migration of records."""
        with patch("invenio_migrator.services.migration.CONFIG", mock_config):
            migration_service.migrate_records(query="test query")

            # Verify correct method calls
            mock_provider.get_records.assert_called_once_with(query="test query")
            assert mock_mapper.map_record.call_count == 2
            assert mock_consumer.create_record.call_count == 2

            # Verify community submission was handled
            assert mock_consumer.create_review_request.call_count == 2
            assert mock_consumer.submit_review.call_count == 2

    def test_migrate_records_dry_run(
        self, migration_service, mock_provider, mock_consumer, mock_mapper
    ):
        """Test dry run mode."""
        migration_service.migrate_records(dry_run=True)

        # Verify provider and mapper were called
        mock_provider.get_records.assert_called_once()
        assert mock_mapper.map_record.call_count == 2

        # Verify consumer was NOT called (dry run)
        mock_consumer.create_record.assert_not_called()
        mock_consumer.create_review_request.assert_not_called()

    def test_migrate_records_with_files(self, migration_service, mock_mapper):
        """Test migration with files enabled."""
        migration_service.migrate_records(include_files=True)

        # Check that mapper was called and files were enabled
        calls = mock_mapper.map_record.call_args_list
        for i, call in enumerate(calls):
            mapped_record = migration_service.mapper.map_record.return_value
            assert mapped_record["files"]["enabled"] is True

    def test_migrate_records_mapping_error(
        self, migration_service, mock_mapper, mock_config
    ):
        """Test handling of mapping errors."""
        # Configure mapper to fail on the second record
        mock_mapper.map_record.side_effect = [
            {
                "access": {"record": "public", "files": "public"},
                "metadata": {"title": "Mapped Record 1"},
                "pids": {"doi": {"identifier": "10.1234/test", "provider": "external"}},
            },
            RecordMappingError("record2", field="title", reason="Invalid title"),
        ]

        with patch("invenio_migrator.services.migration.CONFIG", mock_config):
            # Run migration
            migration_service.migrate_records()

            # Verify first record was created
            migration_service.consumer.create_record.assert_called_once()

    def test_migrate_records_stop_on_error(self, migration_service, mock_mapper):
        """Test migration stops on error when configured to do so."""
        # Configure mapper to fail on the second record
        mock_mapper.map_record.side_effect = [
            {
                "access": {"record": "public", "files": "public"},
                "metadata": {"title": "Mapped Record 1"},
                "pids": {"doi": {"identifier": "10.1234/test", "provider": "external"}},
            },
            RecordMappingError("record2", field="title", reason="Invalid title"),
        ]

        # Configure to stop on error
        with patch(
            "invenio_migrator.services.migration.CONFIG",
            {"MIGRATION_OPTIONS": {"STOP_ON_ERROR": True}},
        ):
            # Migration should raise an error
            with pytest.raises(MigrationError) as exc_info:
                migration_service.migrate_records()

            assert "record2" in str(exc_info.value)
            assert len(exc_info.value.failed_records) == 1

            # Verify first record was created
            migration_service.consumer.create_record.assert_called_once()

    def test_migrate_single_record(
        self, migration_service, mock_provider, mock_consumer, mock_mapper
    ):
        """Test migrating a single record."""
        result = migration_service.migrate_single_record("record1")

        # Verify correct methods were called
        mock_provider.get_record.assert_called_once_with("record1")
        mock_mapper.map_record.assert_called_once()
        mock_consumer.create_record.assert_called_once()

        # Verify result is the created record
        assert result == {"id": "draft-1", "metadata": {"title": "Record 1"}}

    def test_migrate_single_record_not_found(self, migration_service, mock_provider):
        """Test migrating a single record that doesn't exist."""
        mock_provider.get_record.return_value = None

        result = migration_service.migrate_single_record("nonexistent")

        # Verify correct methods were called
        mock_provider.get_record.assert_called_once_with("nonexistent")
        mock_provider.get_record.assert_called_once()

        # Result should be None
        assert result is None

        # Verify mapper and consumer were not called
        migration_service.mapper.map_record.assert_not_called()
        migration_service.consumer.create_record.assert_not_called()

    def test_migrate_single_record_validation_error(
        self, migration_service, mock_mapper
    ):
        """Test validation error when migrating a single record."""
        # Make validation fail
        mock_mapper.validate_mapped_record.return_value = False

        with pytest.raises(ValueError) as exc_info:
            migration_service.migrate_single_record("record1")

        assert "Invalid mapped record" in str(exc_info.value)

        # Verify consumer was not called
        migration_service.consumer.create_record.assert_not_called()

    def test_handle_community_submission(
        self, migration_service, mock_consumer, mock_config
    ):
        """Test handling community submission."""
        with patch("invenio_migrator.services.migration.CONFIG", mock_config):
            created_record = {"id": "draft-1"}
            migration_service._handle_community_submission(created_record)

            # Verify review request and submission
            mock_consumer.create_review_request.assert_called_once_with(
                "draft-1", "test-community"
            )
            mock_consumer.submit_review.assert_called_once_with(
                "draft-1", "Test review content"
            )

    def test_handle_community_submission_no_id(
        self, migration_service, mock_consumer, mock_config
    ):
        """Test community submission handling when draft ID is missing."""
        with patch("invenio_migrator.services.migration.CONFIG", mock_config):
            created_record = {}  # No ID
            migration_service._handle_community_submission(created_record)

            # Verify no review request or submission
            mock_consumer.create_review_request.assert_not_called()
            mock_consumer.submit_review.assert_not_called()

    def test_handle_community_submission_no_community(
        self, migration_service, mock_consumer
    ):
        """Test community submission handling when no community ID configured."""
        with patch("invenio_migrator.services.migration.CONFIG", {}):
            created_record = {"id": "draft-1"}
            migration_service._handle_community_submission(created_record)

            # Verify no review request or submission
            mock_consumer.create_review_request.assert_not_called()
            mock_consumer.submit_review.assert_not_called()

    def test_get_migration_status(
        self, migration_service, mock_provider, mock_consumer, mock_mapper
    ):
        """Test getting migration status."""
        # Configure connection validation responses
        mock_provider.validate_connection.return_value = True
        mock_consumer.validate_connection.return_value = False
        mock_mapper.get_mapping_schema.return_value = {"version": "1.0"}

        # Get status
        status = migration_service.get_migration_status()

        # Validate the response
        assert status["provider"]["connection"] is True
        assert status["consumer"]["connection"] is False
        assert status["mapper"]["schema"] == {"version": "1.0"}
        assert "stop_on_error" in status["config"]

        # Verify calls
        mock_provider.validate_connection.assert_called_once()
        mock_consumer.validate_connection.assert_called_once()
        mock_mapper.get_mapping_schema.assert_called_once()

    def test_get_migration_status_with_errors(
        self, migration_service, mock_provider, mock_consumer
    ):
        """Test getting migration status with connection errors."""
        # Make validate_connection throw exceptions
        mock_provider.validate_connection.side_effect = Exception("Provider error")
        mock_consumer.validate_connection.side_effect = Exception("Consumer error")

        # Get status (should not raise exceptions)
        status = migration_service.get_migration_status()

        # Validate the response
        assert status["provider"]["connection"] is False
        assert status["consumer"]["connection"] is False

    def test_validate_migration_setup_failure(self, migration_service):
        """Test failed migration setup validation."""
        # Mock get_migration_status to return failed connections
        mock_status = {
            "provider": {"connection": False},
            "consumer": {"connection": True},
        }

        migration_service.get_migration_status = MagicMock(return_value=mock_status)

        # Validation should fail for provider
        assert migration_service.validate_migration_setup() is False

        # Test consumer failure
        mock_status["provider"]["connection"] = True
        mock_status["consumer"]["connection"] = False
        assert migration_service.validate_migration_setup() is False

    def test_get_migration_status_with_connection_errors(
        self, migration_service, mock_provider, mock_consumer
    ):
        """Test getting migration status with connection errors."""
        # Make validate_connection throw exceptions
        mock_provider.validate_connection.side_effect = Exception("Provider error")
        mock_consumer.validate_connection.side_effect = Exception("Consumer error")

        # Get status (should not raise exceptions)
        status = migration_service.get_migration_status()

        # Validate the response
        assert status["provider"]["connection"] is False
        assert status["consumer"]["connection"] is False

    def test_validate_migration_setup_success(self, migration_service):
        """Test successful migration setup validation."""
        # Mock get_migration_status to return successful connections
        mock_status = {
            "provider": {"connection": True},
            "consumer": {"connection": True},
        }

        migration_service.get_migration_status = MagicMock(return_value=mock_status)

        # Validate setup
        assert migration_service.validate_migration_setup() is True

    def test_validate_migration_setup_validation_failure(self, migration_service):
        """Test failed migration setup validation."""
        # Mock get_migration_status to return failed connections
        mock_status = {
            "provider": {"connection": False},
            "consumer": {"connection": True},
        }

        migration_service.get_migration_status = MagicMock(return_value=mock_status)

        # Validation should fail for provider
        assert migration_service.validate_migration_setup() is False

        # Test consumer failure
        mock_status["provider"]["connection"] = True
        mock_status["consumer"]["connection"] = False
        assert migration_service.validate_migration_setup() is False


class TestLegacyRecordMapper:
    """Test the legacy RecordMapper class."""

    def test_init(self):
        """Test initialization and deprecation warning."""
        with patch("invenio_migrator.services.migration.logger") as mock_logger:
            RecordMapper()

            # Verify deprecation warning
            mock_logger.warning.assert_called_once()
            assert "deprecated" in mock_logger.warning.call_args[0][0]

    def test_legacy_methods(self):
        """Test legacy method calls."""
        mapper = RecordMapper()

        # Patch the parent methods
        with (
            patch.object(mapper, "_map_single_creator") as mock_creator,
            patch.object(mapper, "_map_subjects") as mock_subjects,
        ):
            creator = {"name": "Test Person"}
            mapper.map_creator(creator)
            mock_creator.assert_called_once_with(creator)

            keywords = ["test", "keyword"]
            mapper.map_subjects(keywords)
            mock_subjects.assert_called_once_with(keywords)
