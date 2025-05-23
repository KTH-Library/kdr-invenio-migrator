"""Custom exceptions for Invenio Migrator following single responsibility principle."""


class InvenioMigratorError(Exception):
    """Base exception for all Invenio Migrator errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class APIClientError(InvenioMigratorError):
    """Exception raised when API client operations fail."""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        self.status_code = status_code
        self.response_data = response_data
        details = f"Status: {status_code}" if status_code else None
        super().__init__(message, details)


class AuthenticationError(APIClientError):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class RecordMappingError(InvenioMigratorError):
    """Exception raised when record mapping fails."""

    def __init__(self, record_id: str, field: str = None, reason: str = None):
        self.record_id = record_id
        self.field = field
        message = f"Failed to map record {record_id}"
        if field:
            message += f" (field: {field})"
        super().__init__(message, reason)


class RecordValidationError(InvenioMigratorError):
    """Exception raised when record validation fails."""

    def __init__(
        self, record_id: str, missing_fields: list = None, invalid_fields: list = None
    ):
        self.record_id = record_id
        self.missing_fields = missing_fields or []
        self.invalid_fields = invalid_fields or []

        details = []
        if self.missing_fields:
            details.append(f"Missing: {', '.join(self.missing_fields)}")
        if self.invalid_fields:
            details.append(f"Invalid: {', '.join(self.invalid_fields)}")

        message = f"Record validation failed for {record_id}"
        super().__init__(message, "; ".join(details) if details else None)


class MigrationError(InvenioMigratorError):
    """Exception raised when migration operations fail."""

    def __init__(self, message: str, failed_records: list = None):
        self.failed_records = failed_records or []
        details = (
            f"Failed records: {len(self.failed_records)}"
            if self.failed_records
            else None
        )
        super().__init__(message, details)


class ConfigurationError(InvenioMigratorError):
    """Exception raised when configuration is invalid."""

    def __init__(self, config_key: str, reason: str = None):
        self.config_key = config_key
        message = f"Configuration error for '{config_key}'"
        super().__init__(message, reason)
