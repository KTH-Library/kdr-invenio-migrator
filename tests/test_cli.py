# filepath: /Users/samk13/Documents/CODE/INVENIO/kth-invenio-migrator/tests/test_smoketest.py
"""Smoke tests for kth-invenio-migrator."""

import io
from contextlib import redirect_stdout

from kth_invenio_migrator.cli import main


def test_main_function():
    """Test that the main function prints the expected welcome message."""
    # Capture stdout
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        main()
    
    # Get the output value
    output = captured_output.getvalue().strip()
    
    # Assert that the output matches what we expect
    assert output == "Hello from kth-invenio-migrator!"