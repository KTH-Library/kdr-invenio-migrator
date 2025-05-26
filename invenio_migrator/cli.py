"""CLI for Invenio Migrator."""

import click
import urllib3

from .services import CliService
from .utils.logger import logger

# Disable SSL warnings for insecure requests InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    "--record",
    "-r",
    help="provide source record id or comma-separated list of record ids to harvest e.g. '1234, 5678, 91011'",
    type=click.STRING,
)
@click.option(
    "--output",
    "-o",
    help="output file to save the harvested records",
    type=click.Path(exists=False),
)
@click.option(
    "--include-files",
    "-f",
    is_flag=True,
    help="include files in the harvested records",
)
def migrate(dry_run, query, output, include_files, record):
    """Fetch records from Zenodo community"""
    # Use the CLI service to handle the migrate command
    click.echo("Fetching records from Zenodo community...", color="green")
    cli_service = CliService()
    cli_service.handle_migrate_command(
        dry_run=dry_run,
        query=query,
        output=output,
        include_files=include_files,
        record_or_records=record,
    )


if __name__ == "__main__":
    migrator()
