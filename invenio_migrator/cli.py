"""CLI for Invenio Migrator."""
import json
import logging
from pathlib import Path

import click

from .clients.zenodo import ZenodoHarvester
from .config import CONFIG
from .utils.logger import setup_logging


@click.group()
def main():
    """Invenio Migrator CLI"""
    setup_logging()


@main.command()
@click.option(
    "--dry-run", "-d", is_flag=True, help="fetch records without submitting to KDR"
)
@click.option(
    "--query",
    "-q",
    help="query results by e.g. date range e.g.: 'metadata.publication_date:{2025-01-01 TO *}'",
    type=click.STRING,
)
@click.option(
    "--output",
    "-o",
    help="output file to save the harvested records",
    type=click.Path(exists=False),
)
def migrate(dry_run, query, output):
    """Fetch records from Zenodo community"""
    # Update config with CLI parameters
    CONFIG["MIGRATION_OPTIONS"]["DRY_RUN"] = dry_run

    logger = logging.getLogger(__name__)
    harvester = ZenodoHarvester()

    try:
        logger.info("Starting harvesting ...")

        for record in harvester.harvest_records(query=query):
            logger.info(
                "Processing record ID: %s, with DOI: %s",
                record["id"],
                record.get("doi"),
            )

            if dry_run:
                logger.debug("Dry run: Would process %s", record["doi"])
                if output:
                    with Path.open(output, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record) + "\n")
                logger.info(json.dumps(record, indent=2))
                continue

            # TODO: Add processing logic here
            logger.info("Fetched record %s", record["doi"])

    except Exception as e:
        logger.error("Harvest failed: %s", str(e))
        if CONFIG["MIGRATION_OPTIONS"]["STOP_ON_ERROR"]:
            raise


if __name__ == "__main__":
    main()
