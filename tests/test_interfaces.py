"""Test the interfaces and abstract base classes."""

from unittest.mock import MagicMock

import pytest

from invenio_migrator.interfaces import (
    BaseAPIClient,
    BaseMigrationService,
    BaseRecordMapper,
    RecordConsumerInterface,
    RecordMapperInterface,
    RecordProviderInterface,
)


class MockAPIClient(BaseAPIClient):
    """Mock implementation of BaseAPIClient for testing."""

    def _setup_session(self):
        self._session = MagicMock()

    def make_request(self, url, **kwargs):
        return {"success": True, "url": url}


class MockRecordProvider(BaseAPIClient):
    """Mock implementation of a record provider."""

    def _setup_session(self):
        self._session = MagicMock()

    def make_request(self, url, **kwargs):
        return {"success": True, "url": url}

    def get_records(self, query=None, **kwargs):
        return [{"id": 1, "title": "Test Record"}]

    def get_record(self, record_id):
        return {"id": record_id, "title": "Test Record"}

    def get_record_count(self, query=None):
        return 1

    def validate_connection(self):
        return True


class MockRecordConsumer(BaseAPIClient):
    """Mock implementation of a record consumer."""

    def _setup_session(self):
        self._session = MagicMock()

    def make_request(self, url, **kwargs):
        return {"success": True, "url": url}

    def create_record(self, record_data):
        return {"id": "new-id", **record_data}

    def update_record(self, record_id, record_data):
        return {"id": record_id, **record_data}

    def delete_record(self, record_id):
        return True

    def get_record(self, record_id):
        return {"id": record_id, "title": "Test Record"}

    def validate_connection(self):
        return True


class MockRecordMapper(BaseRecordMapper):
    """Mock implementation of BaseRecordMapper for testing."""

    def map_record(self, source_record):
        return {
            "metadata": {
                "title": source_record.get("title", "Default Title"),
                "description": source_record.get("description", "Default Description"),
            },
            "access": {"record": "public", "files": "public"},
        }


class TestBaseAPIClient:
    """Test the BaseAPIClient abstract base class."""

    def test_init(self):
        """Test client initialization."""
        client = MockAPIClient("https://example.com", "test-token")
        assert client.base_url == "https://example.com"
        assert client.api_token == "test-token"

    def test_authenticate(self):
        """Test authentication check."""
        client = MockAPIClient("https://example.com", "test-token")
        assert client.authenticate() is True

        client_no_token = MockAPIClient("https://example.com")
        assert client_no_token.authenticate() is False

    def test_make_request(self):
        """Test make_request method."""
        client = MockAPIClient("https://example.com", "test-token")
        result = client.make_request("/endpoint")
        assert result["success"] is True
        assert result["url"] == "/endpoint"


class TestBaseRecordMapper:
    """Test the BaseRecordMapper abstract base class."""

    def test_validate_mapped_record_valid(self):
        """Test validation with valid record."""
        mapper = MockRecordMapper()
        record = {"metadata": {"title": "Test"}, "access": {"record": "public"}}
        assert mapper.validate_mapped_record(record) is True

    def test_validate_mapped_record_invalid(self):
        """Test validation with invalid record."""
        mapper = MockRecordMapper()
        record = {"metadata": {"title": "Test"}}  # Missing access field
        assert mapper.validate_mapped_record(record) is False

        record = {"access": {"record": "public"}}  # Missing metadata field
        assert mapper.validate_mapped_record(record) is False


class TestBaseMigrationService:
    """Test the BaseMigrationService abstract base class."""

    @pytest.fixture
    def mock_migration_service(self):
        """Create a concrete implementation of BaseMigrationService for testing."""

        class MockMigrationService(BaseMigrationService):
            def migrate_records(self, dry_run=False, query=None, **kwargs):
                return [self.migrate_single_record("record-1", dry_run)]

        provider = MockRecordProvider("https://example-source.com", "source-token")
        consumer = MockRecordConsumer("https://example-target.com", "target-token")
        mapper = MockRecordMapper()

        return MockMigrationService(provider, consumer, mapper)

    def test_migrate_single_record(self, mock_migration_service):
        """Test migrating a single record."""
        result = mock_migration_service.migrate_single_record("record-1", dry_run=False)
        assert result["id"] == "new-id"
        assert "metadata" in result
        assert "access" in result

    def test_migrate_single_record_dry_run(self, mock_migration_service):
        """Test migrating a single record in dry run mode."""
        result = mock_migration_service.migrate_single_record("record-1", dry_run=True)
        assert "metadata" in result
        assert "access" in result
        # In dry run, we should get back the mapped record without creating it
        assert "new-id" not in result


def test_protocol_conformance():
    """Test that our mock implementations conform to the protocols."""
    provider = MockRecordProvider("https://example.com", "token")
    assert isinstance(provider, RecordProviderInterface)

    consumer = MockRecordConsumer("https://example.com", "token")
    assert isinstance(consumer, RecordConsumerInterface)

    mapper = MockRecordMapper()
    assert isinstance(mapper, RecordMapperInterface)
