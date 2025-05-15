"""Smoke tests for invenio-migrator."""

from click.testing import CliRunner

from invenio_migrator.cli import main


def test_main_help():
    """Test that the main CLI command works and shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Invenio Migrator CLI" in result.output


def test_migrate_command():
    """Test the migrate command."""
    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--dry-run"])
    assert result.exit_code == 0
    assert "Starting migration" in result.output
    assert "Dry run enabled" in result.output
