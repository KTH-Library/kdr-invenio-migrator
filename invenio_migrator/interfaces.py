"""Interfaces and abstract base classes for Invenio Migrator following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional, Protocol, runtime_checkable


@runtime_checkable
class APIClientInterface(Protocol):
    """Protocol defining the interface for API clients."""

    def make_request(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request to the API."""
        ...

    def authenticate(self) -> bool:
        """Authenticate with the API."""
        ...

    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the API."""
        ...


@runtime_checkable
class RecordProviderInterface(Protocol):
    """Protocol for record providers (source systems)."""

    def get_records(
        self, query: Optional[str] = None, **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """Get records from the provider."""
        ...

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        ...

    def get_record_count(self, query: Optional[str] = None) -> int:
        """Get the total count of records matching the query."""
        ...

    def validate_connection(self) -> bool:
        """Validate the connection to the provider."""
        ...


@runtime_checkable
class RecordConsumerInterface(Protocol):
    """Protocol for record consumers (target systems)."""

    def create_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        ...

    def update_record(
        self, record_id: str, record_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing record."""
        ...

    def delete_record(self, record_id: str) -> bool:
        """Delete a record."""
        ...

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        ...

    def validate_connection(self) -> bool:
        """Validate the connection to the consumer."""
        ...


@runtime_checkable
class RecordMapperInterface(Protocol):
    """Protocol for mapping records between formats."""

    def map_record(self, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a record from source format to target format."""
        ...

    def validate_mapped_record(self, mapped_record: Dict[str, Any]) -> bool:
        """Validate a mapped record."""
        ...

    def get_mapping_schema(self) -> Dict[str, Any]:
        """Get the mapping schema used by this mapper."""
        ...

    def validate_source_record(self, source_record: Dict[str, Any]) -> bool:
        """Validate a source record before mapping."""
        ...


@runtime_checkable
class MigrationServiceInterface(Protocol):
    """Protocol for migration services."""

    def migrate_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Migrate records from source to target."""
        ...

    def migrate_single_record(
        self, record_id: str, dry_run: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Migrate a single record."""
        ...

    def get_migration_status(self) -> Dict[str, Any]:
        """Get the current migration status."""
        ...

    def validate_migration_setup(self) -> bool:
        """Validate that migration can proceed."""
        ...


# Abstract base classes for concrete implementations


class BaseAPIClient(ABC):
    """Base API client with common functionality."""

    def __init__(self, base_url: str, api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self._session = None

    @abstractmethod
    def _setup_session(self) -> None:
        """Setup the HTTP session with authentication and headers."""
        pass

    @abstractmethod
    def make_request(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request to the API."""
        pass

    def authenticate(self) -> bool:
        """Authenticate with the API."""
        return self.api_token is not None

    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the API."""
        try:
            # Default implementation - subclasses can override
            url = f"{self.base_url}/health"
            return self.make_request(url)
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class BaseRecordMapper(ABC):
    """Base record mapper with common validation."""

    @abstractmethod
    def map_record(self, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a record from source format to target format."""
        pass

    def validate_mapped_record(self, mapped_record: Dict[str, Any]) -> bool:
        """Validate a mapped record has required fields."""
        required_fields = ["metadata", "access"]
        return all(field in mapped_record for field in required_fields)

    def get_mapping_schema(self) -> Dict[str, Any]:
        """Get the mapping schema used by this mapper."""
        return {
            "source_format": "unknown",
            "target_format": "unknown",
            "version": "1.0",
            "required_fields": ["metadata", "access"],
        }

    def validate_source_record(self, source_record: Dict[str, Any]) -> bool:
        """Validate a source record before mapping."""
        # Basic validation - subclasses can override
        return isinstance(source_record, dict) and len(source_record) > 0


class BaseMigrationService(ABC):
    """Base migration service with common workflow."""

    def __init__(
        self,
        provider: RecordProviderInterface,
        consumer: RecordConsumerInterface,
        mapper: RecordMapperInterface,
    ):
        self.provider = provider
        self.consumer = consumer
        self.mapper = mapper

    @abstractmethod
    def migrate_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Migrate records from source to target."""
        pass

    def migrate_single_record(
        self, record_id: str, dry_run: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Migrate a single record."""
        source_record = self.provider.get_record(record_id)
        if not source_record:
            return None

        mapped_record = self.mapper.map_record(source_record)
        if not self.mapper.validate_mapped_record(mapped_record):
            raise ValueError(f"Invalid mapped record for ID: {record_id}")

        if dry_run:
            return mapped_record

        return self.consumer.create_record(mapped_record)
