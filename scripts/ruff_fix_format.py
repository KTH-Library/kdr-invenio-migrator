import logging
import subprocess

logger = logging.getLogger()


def main():
    """
    Run ruff check and ruff format on the current directory.
    """
    try:
        subprocess.run(["uv", "run", "ruff", "check", "--fix", "."], check=True)
        subprocess.run(["uv", "run", "ruff", "format", "."], check=True)
    except Exception:
        return
