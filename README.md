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

run `cp .env.example .env` file in the root directory of the project and update the environment variables as needed:


## Usage

Before running the migration, make sure to double check the configurations in `invenio_migrator/config.py`
Make sure to provide the community id in the `COMMUNITY_ID` variable NOT the community name!
you can retrieve the community id by:
- navigating to the target community
- open the Chrome dev tools under the network tab and filter by `Fetch/XHR`
- refresh the page
- look for the community id in the Headers tab under Request URL 
- you will see something like this:
`https://127.0.0.1:5000/api/communities/21f6dd7d-f98d-489e-b658-3db9aa459f13/records?q=&sort=newest&page=1&size=10`
- grab the id `21f6dd7d-f98d-489e-b658-3db9aa459f13` and add it to the `COMMUNITY_ID` variable in the `config.py` file.

```bash
To check available commands, run:

```bash
uv run invenio-migrator --help
```
To run the records migration, use the following command:

```bash
# list all available commands
uv run invenio-migrator migrate --help

# run the migration with specific query as dry run
uv run invenio-migrator migrate -q "metadata.publication_date:{2025-01-01 TO *}" -d
```
This will start the migration process and print the progress to the console.
Note that the `-q` option is used to query the records to be migrated. In this case, it will only migrate records with a publication date after January 1, 2025.
the `-d` option is used to run the migration in dry run mode, which means it will not actually create any records in the destination but will print the records that would be created.


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


## TODOS
- [x] Add submit to community step.
- [x] Add approve step.
- [ ] Add a publish as cli option.
- [x] Add single record cli command.
- [x] Refactor the code for source and destination to be more generic.
- [x] Make the fields mappings more generic.
- [ ] First Zenodo request should save the response to a file and then read from it (not DB for simplicity) and only fetch if the file is not present or empty.
- [ ] Add cli command to remove all draft records (currently using Postman action).
