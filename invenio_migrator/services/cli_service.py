"""CLI Service for handling command-line operations following SOLID principles."""

from typing import Optional

from requests.exceptions import HTTPError

from ..errors import InvenioMigratorError, MigrationError
from ..utils.logger import logger
from .migration import MigrationService


class CliService:
    """Service for handling command-line operations with dependency injection."""

    def __init__(self, migration_service: Optional[MigrationService] = None):
        """Initialize the CLI service.

        Args:
            migration_service: Optionally inject a custom migration service
        """
        self.logger = logger
        self.migration_service = migration_service or MigrationService()

    def handle_migrate_command(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        output: Optional[str] = None,
        include_files: bool = False,
        record_or_records: Optional[str] = None,
        **kwargs: Optional[dict],
    ) -> None:
        """Handle the migrate command from CLI.

        Args:
            dry_run: If True, fetches records without submitting to target.
            query: Optional query string to filter results.
            output: Optional file path to save the harvested records.
            include_files: Whether to include files in migration.
            record_or_records: Optional specific record ID(s) to migrate.
            **kwargs: Additional parameters for migration.
        """
        self.logger.debug(
            "Processing migrate command with options: dry_run=%s, query=%s, output=%s, include_files=%s, record_or_records=%s",
            dry_run,
            query,
            output,
            include_files,
            record_or_records,
        )

        try:
            if record_or_records:
                record_or_records = record_or_records.strip().split(",")
                record_or_records = [r.strip() for r in record_or_records if r.strip()]
                if not record_or_records:
                    self.logger.warning("No valid record IDs provided, skipping")
                    return
            # Handle output to file if specified
            if output:
                self._handle_output_to_file(
                    output_file=output,
                    query=query,
                    include_files=include_files,
                    record_or_records=record_or_records,
                    **kwargs,
                )
            else:
                # Standard migration workflow
                self.migration_service.migrate_records(
                    dry_run=dry_run,
                    query=query,
                    include_files=include_files,
                    record_or_records=record_or_records,
                    **kwargs,
                )

        except MigrationError as e:
            self.logger.error("Migration failed: %s", e.message)
            if e.details:
                self.logger.error("Details: %s", e.details)
            if hasattr(e, "failed_records") and e.failed_records:
                self.logger.error(
                    "Failed record IDs: %s", [r["id"] for r in e.failed_records]
                )
            raise

        except HTTPError as e:
            self.logger.error("HTTP error during migration: %s", e)
            raise InvenioMigratorError("Network error during migration", str(e))

        except Exception as e:
            self.logger.error("Unexpected error during migration: %s", e)
            raise InvenioMigratorError("Unexpected migration error", str(e))

    def _handle_output_to_file(
        self,
        output_file: str,
        query: Optional[str] = None,
        include_files: bool = False,
        **kwargs,
    ) -> None:
        """Handle saving migration output to a file instead of migrating."""
        import json
        from pathlib import Path

        try:
            self.logger.info(f"Saving records to file: {output_file}")

            # Get records but don't migrate them
            records = list(
                self.migration_service.provider.get_records(query=query, **kwargs)
            )

            # Map records for preview
            mapped_records = []
            for record in records:
                try:
                    mapped_record = self.migration_service.mapper.map_record(record)
                    if include_files and "files" in mapped_record:
                        mapped_record["files"]["enabled"] = include_files
                    mapped_records.append(
                        {
                            "source_id": record.get("id"),
                            "source_record": record,
                            "mapped_record": mapped_record,
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to map record {record.get('id')}: {e}")
                    mapped_records.append(
                        {
                            "source_id": record.get("id"),
                            "source_record": record,
                            "mapping_error": str(e),
                        }
                    )

            # Save to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(mapped_records, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(mapped_records)} records to {output_file}")

        except Exception as e:
            self.logger.error(f"Error saving to file: {e}")
            raise InvenioMigratorError(
                f"Failed to save records to file: {output_file}", str(e)
            )
