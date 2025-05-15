import subprocess


def main():
    """
    Run ruff check and ruff format on the current directory.
    """
    subprocess.run(["uv", "run", "ruff", "check", "--fix", "."], check=True)
    subprocess.run(["uv", "run", "ruff", "format", "."], check=True)
