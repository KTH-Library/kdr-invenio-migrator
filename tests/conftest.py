"""Pytest fixtures for invenio-migrator tests."""

import io
import os
import pathlib
import shutil
import sys
import uuid
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env_variables():
    """Fixture to provide mocked environment variables."""
    env_vars = {
        "SOURCE_API_TOKEN": "mock_zenodo_token",
        "SOURCE_COMMUNITY_API_URL": "https://mock.zenodo.org/api/records",
        "KDR_API_TOKEN": "mock_token",
        "KDR_COMMUNITY_URL": "https://mock.kth.se/api/invenio",
        "INCLUDE_RECORD_FILES": "false",
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def sample_zenodo_record():
    """Fixture to provide a sample Zenodo record for testing."""
    return {
        "created": "2025-05-14T12:59:35.173216+00:00",
        "modified": "2025-05-14T12:59:35.427103+00:00",
        "id": 15411009,
        "conceptrecid": "15411008",
        "doi": "10.5281/zenodo.15411009",
        "conceptdoi": "10.5281/zenodo.15411008",
        "doi_url": "https://doi.org/10.5281/zenodo.15411009",
        "metadata": {
            "title": "Find and explore data presentation for KTH Library webinar on May 15th 2025",
            "doi": "10.5281/zenodo.15411009",
            "publication_date": "2025-05-14",
            "description": "<h1>Discover and explore research data</h1>\n<p>Example test description</p>",
            "access_right": "open",
            "creators": [
                {
                    "name": "Andrén, Lina J.",
                    "affiliation": "KTH Royal Institute of Technology",
                    "orcid": "0000-0002-7539-3203",
                },
                {
                    "name": "Vesterlund, Mattias",
                    "affiliation": "KTH Royal Institute of Technology",
                    "orcid": "0000-0001-9471-6592",
                },
            ],
            "resource_type": {"title": "Presentation", "type": "presentation"},
            "license": {"id": "cc-by-4.0"},
            "communities": [{"id": "kth"}],
        },
        "title": "Find and explore data presentation for KTH Library webinar on May 15th 2025",
        "links": {
            "self": "https://zenodo.org/api/records/15411009",
            "self_html": "https://zenodo.org/records/15411009",
            "doi": "https://doi.org/10.5281/zenodo.15411009",
        },
        "recid": "15411009",
        "files": [
            {
                "id": "ca3799c8-b6a7-411b-8041-604b19b684b5",
                "key": "Finding_and_exploring_data.pdf",
                "size": 1498808,
                "checksum": "md5:7bf6bbbc35429543fdf07552f73aaceb",
                "links": {
                    "self": "https://zenodo.org/api/records/15411009/files/Finding_and_exploring_data.pdf/content"
                },
            }
        ],
        "status": "published",
    }


@pytest.fixture
def capture_stdout(monkeypatch):
    """Fixture to capture stdout for testing CLI output."""

    output = io.StringIO()
    monkeypatch.setattr(sys, "stdout", output)
    yield output


@pytest.fixture
def tests_tmp_path(request):
    """Create a temporary directory inside tests/test-temp/ for a test and cleans it up."""
    # Get the path to the 'tests' directory where conftest.py is located
    tests_dir = pathlib.Path(__file__).parent
    base_temp_dir = tests_dir / "test-temp"

    # Create the base temporary directory if it doesn't exist
    base_temp_dir.mkdir(parents=True, exist_ok=True)

    # Create a unique directory for the current test using UUID
    unique_subdir_name = uuid.uuid4().hex
    test_specific_dir = base_temp_dir / unique_subdir_name
    test_specific_dir.mkdir(parents=True, exist_ok=True)

    def cleanup():
        if test_specific_dir.exists():
            shutil.rmtree(test_specific_dir)

    request.addfinalizer(cleanup)
    return test_specific_dir
