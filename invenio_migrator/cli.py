"""CLI for Invenio Migrator."""

import click

from .services import CliService
from .utils.logger import logger


@click.group()
@click.version_option()
def migrator():
    """Invenio Migrator CLI
    this CLI is used to migrate records from Zenodo to InvenioRDM instance.
    """
    logger.info("Invenio Migrator CLI started")


@migrator.command()
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
    # Use the CLI service to handle the migrate command
    cli_service = CliService()
    cli_service.handle_migrate_command(dry_run=dry_run, query=query, output=output)


if __name__ == "__main__":
    migrator()
