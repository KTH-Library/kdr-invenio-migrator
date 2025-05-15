import click

from .config import CONFIG


@click.group()
def main():
    """Invenio Migrator CLI
    A command-line interface for migrating records from Zenodo to InvenioRDM.
    run `invenio-migrator migrate` to start the migration process.
    """


@main.command()
@click.option("--dry-run", is_flag=True, help="Validate without actual migration")
@click.option(
    "--start-date", default=CONFIG["START_DATE"], help="Filter records after this date"
)
@click.option(
    "--end-date", default=CONFIG["END_DATE"], help="Filter records before this date"
)
def migrate(dry_run, start_date, end_date):
    """Execute migration workflow"""
    # Initialize clients
    # zenodo = ZenodoClient(token=CONFIG["ZENODO_API_TOKEN"])
    # invenio = InvenioClient(token=CONFIG["KDR_API_TOKEN"])

    # Implement migration logic here
    click.echo(f"Starting migration from {start_date} to {end_date}")
    if dry_run:
        click.secho("Dry run enabled - no changes will be committed", fg="yellow")


if __name__ == "__main__":
    main()
