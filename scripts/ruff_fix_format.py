import subprocess


def main():
    """Run ruff check and format commands."""
    subprocess.run(["uv", "run", "ruff", "check", "--fix", "."], check=True)
    subprocess.run(["uv", "run", "ruff", "format", "."], check=True)
