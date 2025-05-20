"""CLI Service for handling command-line operations."""

from typing import Optional

from ..utils.logger import logger
from .migration import MigrationService


class CliService:
    """Service for handling command-line operations."""

    def __init__(self):
        """Initialize the CLI service."""
        self.logger = logger
        self.migration_service = MigrationService()

    def handle_migrate_command(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        output: Optional[str] = None,
    ) -> None:
        """
        Handle the migrate command from CLI.

        Args:
            dry_run: If True, fetches records without submitting to KDR.
            query: Optional query string to filter results.
            output: Optional file path to save the harvested records.
        """
        self.logger.debug(
            "Processing migrate command with options: dry_run=%s, query=%s, output=%s",
            dry_run,
            query,
            output,
        )

        # Delegate to the migration service
        self.migration_service.process_records(dry_run=dry_run, query=query)
