"""Smoke tests for invenio-migrator."""

from click.testing import CliRunner

from invenio_migrator.cli import migrator


def test_main_help():
    """Test that the main CLI command works and shows help."""
    runner = CliRunner()
    result = runner.invoke(migrator, ["--help"])
    assert result.exit_code == 0
    assert "Invenio Migrator CLI" in result.output


def test_migrate_command(mocker):
    """Test the migrate command."""
    # Mock the CliService to control its behavior
    mock_cli_service = mocker.patch("invenio_migrator.cli.CliService")
    mock_cli_service_instance = mock_cli_service.return_value

    runner = CliRunner()
    result = runner.invoke(migrator, ["migrate", "--dry-run"])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the CliService was called with correct parameters
    mock_cli_service_instance.handle_migrate_command.assert_called_once_with(
        dry_run=True,
        query=None,
        output=None,
        include_files=False,
        record_or_records=None,
    )


def test_migrate_with_query(mocker):
    """Test migrate command with query parameter."""
    # Mock the CliService
    mock_cli_service = mocker.patch("invenio_migrator.cli.CliService")
    mock_cli_service_instance = mock_cli_service.return_value

    runner = CliRunner()
    query = "metadata.publication_date:{2025-01-01 TO *}"
    result = runner.invoke(migrator, ["migrate", "--dry-run", "--query", query])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the CliService was called with correct parameters
    mock_cli_service_instance.handle_migrate_command.assert_called_once_with(
        dry_run=True,
        query=query,
        output=None,
        include_files=False,
        record_or_records=None,
    )


def test_migrate_with_output_file(tests_tmp_path, mocker):
    """Test migrate command with output file."""
    # Mock the CliService
    mock_cli_service = mocker.patch("invenio_migrator.cli.CliService")
    mock_cli_service_instance = mock_cli_service.return_value

    runner = CliRunner()
    output_file = tests_tmp_path / "output.jsonl"
    result = runner.invoke(
        migrator,
        ["migrate", "--dry-run", "--output", str(output_file), "--include-files"],
    )

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the CliService was called with correct parameters
    mock_cli_service_instance.handle_migrate_command.assert_called_once_with(
        dry_run=True,
        query=None,
        output=str(output_file),
        include_files=True,
        record_or_records=None,
    )


def test_sample_zenodo_record(sample_zenodo_record):
    """Test that the sample Zenodo record has the expected structure."""
    assert "doi" in sample_zenodo_record
    assert sample_zenodo_record["doi"] == "10.5281/zenodo.15411009"
    assert "metadata" in sample_zenodo_record
    assert "title" in sample_zenodo_record["metadata"]
    assert "creators" in sample_zenodo_record["metadata"]
    assert len(sample_zenodo_record["metadata"]["creators"]) == 2
    assert "files" in sample_zenodo_record
    assert len(sample_zenodo_record["files"]) == 1
    assert sample_zenodo_record["files"][0]["key"] == "Finding_and_exploring_data.pdf"
