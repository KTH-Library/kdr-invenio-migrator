"""Pytest fixtures for kth-invenio-migrator tests."""

import os
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_env_variables():
    """Fixture to provide mocked environment variables."""
    env_vars = {
        "ZENODO_API_TOKEN": "mock_zenodo_token",
        "ZENODO_COMMUNITY_API_URL": "https://mock.zenodo.org/api/records",
        "KTH_KDR_API_TOKEN": "mock_kth_token",
        "KTH_KDR_COMMUNITY_URL": "https://mock.kth.se/api/invenio",
        "INCLUDE_RECORD_FILES": "false",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_zenodo_record():
    """Fixture to provide a sample Zenodo record for testing."""
    return {
        "id": 12345,
        "metadata": {
            "title": "Test Dataset",
            "description": "This is a test dataset for unit testing",
            "creators": [{"name": "Test, User", "affiliation": "KTH"}],
            "publication_date": "2023-05-15",
            "resource_type": {"type": "dataset"},
        },
    }


@pytest.fixture
def capture_stdout(monkeypatch):
    """Fixture to capture stdout for testing CLI output."""
    import io

    output = io.StringIO()

    class MockStdout:
        def write(self, text):
            output.write(text)

        def flush(self):
            pass

    monkeypatch.setattr("sys.stdout", MockStdout())
    return output
