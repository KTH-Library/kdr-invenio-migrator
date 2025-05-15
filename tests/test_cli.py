"""Smoke tests for invenio-migrator."""

from click.testing import CliRunner

from invenio_migrator.cli import main


def test_main_help():
    """Test that the main CLI command works and shows help."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Invenio Migrator CLI" in result.output


def test_migrate_command(mocker):
    """Test the migrate command."""
    # Mock the logger to capture the log messages
    mock_logger = mocker.patch("invenio_migrator.cli.logging.getLogger")
    mock_logger_instance = mock_logger.return_value

    # Mock the ZenodoHarvester to control its behavior
    mock_harvester = mocker.patch("invenio_migrator.cli.ZenodoHarvester")
    mock_harvester_instance = mock_harvester.return_value
    mock_harvester_instance.harvest_records.return_value = []

    runner = CliRunner()
    result = runner.invoke(main, ["migrate", "--dry-run"])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the correct log messages were issued
    mock_logger_instance.info.assert_any_call("Starting harvesting ...")


def test_migrate_with_query(mocker):
    """Test migrate command with query parameter."""
    # Mock the logger
    mock_logger = mocker.patch("invenio_migrator.cli.logging.getLogger")
    mock_logger_instance = mock_logger.return_value

    # Mock the ZenodoHarvester
    mock_harvester = mocker.patch("invenio_migrator.cli.ZenodoHarvester")
    mock_harvester_instance = mock_harvester.return_value
    mock_harvester_instance.harvest_records.return_value = []

    runner = CliRunner()
    query = "metadata.publication_date:{2025-01-01 TO *}"
    result = runner.invoke(main, ["migrate", "--dry-run", "--query", query])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify logging
    mock_logger_instance.info.assert_any_call("Starting harvesting ...")

    # Check that the query was passed to harvest_records
    mock_harvester_instance.harvest_records.assert_called_once_with(query=query)


def test_migrate_with_output_file(tmp_path, mocker):
    """Test migrate command with output file."""
    # Mock file operations
    mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())

    # Mock the ZenodoHarvester
    mock_harvester = mocker.patch("invenio_migrator.cli.ZenodoHarvester")
    mock_harvester_instance = mock_harvester.return_value
    sample_record = {"id": 123, "doi": "10.5281/zenodo.123456"}
    mock_harvester_instance.harvest_records.return_value = [sample_record]

    runner = CliRunner()
    output_file = tmp_path / "output.jsonl"
    result = runner.invoke(main, ["migrate", "--dry-run", "--output", str(output_file)])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify file was opened for writing
    mock_open.assert_called_once_with(mocker.ANY, "a", encoding="utf-8")


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
