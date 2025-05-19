# KTH Invenio Migrato

Invenio Migrator is a tool for migrating data from Zenodo to KTH datarepository.

## Installation
Make sure you have Python 3.12 or later installed.
You have uv installed in your environment. see: https://docs.astral.sh/uv/getting-started/installation/

```bash
uv venv
source .venv/bin/activate
uv sync -n
```

## Configuration

run `cp .env.example .env` file in the root directory of the project and add the following environment variables:

```toml
# Zenodo API token
SOURCE_API_TOKEN=your_zenodo_api_token
# Zenodo COMMUNITY API URL
SOURCE_COMMUNITY_API_URL=https://zenodo.org/api/records
# KDR API token
KDR_API_TOKEN=your_kdr_api_token
# KDR API URL
KDR_COMMUNITY_URL=https://kth.diva-portal.org/smash/api/invenio
# INCLUDE RECORD FILES
INCLUDE_RECORD_FILES=false
```

## Usage
To run the migration, use the following command:

```bash
uv run invenio-migrator migrate -q "metadata.publication_date:{2025-01-01 TO *}" -d
```
This will start the migration process and print the progress to the console.
Note that the `-q` option is used to query the records to be migrated. In this case, it will only migrate records with a publication date after January 1, 2025.


formatting the repo:

```bash
uv run format
# this command is replacing the following commands:
# uv run ruff check --fix .
# uv run ruff format .
```

## Testing
To run the tests, use the following command:

```bash
uv run pytest tests
```
