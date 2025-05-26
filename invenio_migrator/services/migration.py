"""Migration service for handling record migration following SOLID principles."""

from typing import Any, Dict, Optional

from ..clients.target import InvenioRDMClient
from ..clients.zenodo import ZenodoClient
from ..config import CONFIG
from ..errors import MigrationError, RecordMappingError, RecordValidationError
from ..interfaces import (
    BaseMigrationService,
    RecordConsumerInterface,
    RecordMapperInterface,
    RecordProviderInterface,
)
from ..mappers import ZenodoToInvenioRDMMapper
from ..utils.logger import logger


class MigrationService(BaseMigrationService):
    """Service for handling migration of records from external sources using dependency injection."""

    def __init__(
        self,
        provider: Optional[RecordProviderInterface] = None,
        consumer: Optional[RecordConsumerInterface] = None,
        mapper: Optional[RecordMapperInterface] = None,
    ):
        """Initialize migration service with dependency injection.

        Args:
            provider: Source system for records (defaults to ZenodoClient)
            consumer: Target system for records (defaults to InvenioRDMClient)
            mapper: Record mapper (defaults to ZenodoToInvenioRDMMapper)
        """
        # Use default implementations if not provided
        provider = provider or ZenodoClient()
        consumer = consumer or InvenioRDMClient()
        mapper = mapper or ZenodoToInvenioRDMMapper()

        super().__init__(provider, consumer, mapper)
        self.logger = logger
        self.stop_on_error = CONFIG["MIGRATION_OPTIONS"]["STOP_ON_ERROR"]

    def migrate_records(
        self,
        dry_run: bool = False,
        query: Optional[str] = None,
        include_files: bool = False,
        **kwargs: Any,
    ) -> None:
        """Migrate records from source to target with error handling and progress tracking."""
        self.logger.info("Starting record migration...")

        failed_records = []
        success_count = 0

        try:
            # Get records from provider
            records = self.provider.get_records(query=query, **kwargs)

            for record in records:
                if not record:
                    self.logger.warning("Empty record encountered, skipping")
                    continue

                record_id = record.get("id", "unknown")

                try:
                    # Map the record
                    mapped_record = self.mapper.map_record(record)

                    # Update files configuration
                    if "files" in mapped_record:
                        mapped_record["files"]["enabled"] = include_files

                    if dry_run:
                        self.logger.info(f"[DRY RUN] Would migrate record {record_id}")
                        self.logger.debug(f"Mapped record: {mapped_record}")
                        success_count += 1
                        continue

                    # Create record in target system
                    created_record = self.consumer.create_record(mapped_record)

                    # Handle community submission if target is InvenioRDM
                    if isinstance(self.consumer, InvenioRDMClient):
                        self._handle_community_submission(created_record)

                    success_count += 1
                    self.logger.info(f"Successfully migrated record {record_id}")

                except (RecordMappingError, RecordValidationError) as e:
                    self.logger.warning(f"Failed to process record {record_id}: {e}")
                    failed_records.append({"id": record_id, "error": str(e)})

                    if CONFIG["MIGRATION_OPTIONS"]["STOP_ON_ERROR"]:
                        raise MigrationError(
                            f"Migration stopped due to error in record {record_id}",
                            failed_records=failed_records,
                        )

                except Exception as e:
                    self.logger.error(
                        f"Unexpected error processing record {record_id}: {e}"
                    )
                    failed_records.append({"id": record_id, "error": str(e)})

                    if self.stop_on_error:
                        raise MigrationError(
                            f"Migration stopped due to unexpected error in record {record_id}",
                            failed_records=failed_records,
                        )

        except Exception as e:
            if isinstance(e, MigrationError):
                raise
            raise MigrationError(
                f"Migration failed: {e}", failed_records=failed_records
            )

        # Log final results
        self.logger.info(
            f"Migration completed. Success: {success_count}, Failed: {len(failed_records)}"
        )

        if failed_records:
            self.logger.warning(f"Failed records: {[r['id'] for r in failed_records]}")

    def _handle_community_submission(self, created_record: Dict[str, Any]) -> None:
        """Handle community submission workflow for InvenioRDM records."""
        try:
            draft_id = created_record.get("id")
            if not draft_id:
                self.logger.warning("No draft ID found in created record")
                return

            community_id = CONFIG.get("TARGET_COMMUNITY_ID")
            if not community_id:
                self.logger.warning(
                    "No community ID configured, skipping community submission"
                )
                return

            # Create review request
            self.consumer.create_review_request(draft_id, community_id)

            # Submit for review
            review_content = CONFIG.get(
                "COMMUNITY_REVIEW_CONTENT", "Auto-migrated record"
            )
            self.consumer.submit_review(draft_id, review_content)

            self.logger.debug(f"Community submission completed for draft {draft_id}")

        except Exception as e:
            self.logger.warning(f"Community submission failed: {e}")
            # Don't raise - record was created successfully

    def get_migration_status(self) -> Dict[str, Any]:
        """Get the current migration status.

        Returns:
            Dictionary with migration status information
        """
        status = {
            "provider": {
                "type": self.provider.__class__.__name__,
                "connection": False,
            },
            "consumer": {
                "type": self.consumer.__class__.__name__,
                "connection": False,
            },
            "mapper": {
                "type": self.mapper.__class__.__name__,
                "schema": self.mapper.get_mapping_schema(),
            },
            "config": {
                "stop_on_error": self.stop_on_error,
            },
        }

        # Test provider connection
        try:
            status["provider"]["connection"] = self.provider.validate_connection()
        except Exception as e:
            self.logger.error(f"Provider connection test failed: {e}")

        # Test consumer connection
        try:
            status["consumer"]["connection"] = self.consumer.validate_connection()
        except Exception as e:
            self.logger.error(f"Consumer connection test failed: {e}")

        return status

    def validate_migration_setup(self) -> bool:
        """Validate that migration can proceed.

        Returns:
            True if the migration setup is valid, False otherwise
        """
        status = self.get_migration_status()

        # Check provider connection
        if not status["provider"]["connection"]:
            self.logger.error("Provider connection validation failed")
            return False

        # Check consumer connection
        if not status["consumer"]["connection"]:
            self.logger.error("Consumer connection validation failed")
            return False

        return True


# Legacy class for backward compatibility
class RecordMapper(ZenodoToInvenioRDMMapper):
    """Legacy RecordMapper class for backward compatibility."""

    def __init__(self):
        super().__init__()
        logger.warning(
            "RecordMapper is deprecated, use ZenodoToInvenioRDMMapper instead"
        )

    def map_creator(self, creator: Dict) -> Dict:
        """Legacy method for backward compatibility."""
        return self._map_single_creator(creator)

    def map_subjects(self, keywords: list) -> list:
        """Legacy method for backward compatibility."""
        return self._map_subjects(keywords)
