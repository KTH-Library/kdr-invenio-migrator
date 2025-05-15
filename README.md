# KTH Invenio Migrator

KTH Invenio Migrator is a tool for migrating data from Zenodo to KTH datarepository.

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
ZENODO_API_TOKEN=your_zenodo_api_token
# Zenodo COMMUNITY API URL
ZENODO_COMMUNITY_API_URL=https://zenodo.org/api/records
# KTH KDR API token
KTH_KDR_API_TOKEN=your_kth_kdr_api_token
# KTH KDR API URL
KTH_KDR_COMMUNITY_URL=https://kth.diva-portal.org/smash/api/invenio
# INCLUDE RECORD FILES
INCLUDE_RECORD_FILES=false
```

## Usage
To run the migration, use the following command:

```bash
uv run kth-invenio-migrator
```
This will start the migration process and print the progress to the console.
You can also specify the number of records to migrate by adding the `--limit` option:

```bash
uv run kth-invenio-migrator --limit 10
```
This will migrate only the first 10 records from Zenodo to KTH Invenio.
You can also specify the starting record by adding the `--start` option:

```bash
uv run kth-invenio-migrator --start 100
```
This will start the migration from the 100th record in Zenodo.

You can also specify the output file by adding the `--output` option:
```bash
uv run kth-invenio-migrator --output output.json
```

formatting the repo:

```bash
uv run ruff check --fix .
uv run ruff format .
```