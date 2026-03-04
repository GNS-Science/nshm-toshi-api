# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`nshm-toshi-api` is a GraphQL API (Flask + Graphene) deployed as an AWS Lambda function via the Serverless Framework. It serves as the object store for New Zealand NSHM (National Seismic Hazard Model) experiments and outputs — storing task metadata, file references, and computation results in DynamoDB + S3, with Elasticsearch for search.

## Commands

### Setup
```bash
poetry install        # Install Python dependencies
yarn install          # Install Node/Serverless dependencies (requires Node 22, yarn 2/berry)
yarn sls dynamodb install  # Install DynamoDB local plugin (Java required)
```

### Running Tests
```bash
poetry run pytest                          # Run all tests (requires TESTING=1, SLS_OFFLINE=1 in .env)
poetry run pytest graphql_api/tests/test_schema.py  # Run a single test file
poetry run pytest -k "test_name"           # Run tests matching a pattern
```

Tests use `moto` to mock AWS services. The `.env.tests` file is auto-loaded by `conftest.py`. Ensure your `.env` contains:
```
SLS_OFFLINE=1
TESTING=1
```

### Linting & Formatting
```bash
poetry run black graphql_api               # Format code (120 char line length)
poetry run isort graphql_api               # Sort imports
poetry run flake8 graphql_api              # Lint
```

### Local Development (Smoketest)
```bash
yarn sls dynamodb start --stage local &
yarn sls s3 start &
poetry run yarn sls wsgi serve             # Starts Flask on http://localhost:5000/graphql
```
Requires `.env` with `SLS_OFFLINE=1`, `TESTING=0`, `TOSHI_FIX_RANDOM_SEED=1`, `FIRST_DYNAMO_ID=0`.

Elasticsearch must also be running locally:
```bash
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.1.0
```

### Security Auditing
```bash
poetry export --all-groups > audit.txt
poetry run pip-audit -r audit.txt -s pypi --require-hashes
```

## Architecture

### Layered Structure

```
graphql_api/
  api.py           # Flask app entry point; registers GraphQL route, runs DB migrations
  config.py        # All env-var config (IS_OFFLINE, TESTING, ES_*, S3_*, DB_*)
  schema/          # Graphene schema definitions
    schema.py      # Root Query + Mutation types; wires everything together
    custom/        # Domain-specific types (GeneralTask, RuptureSet, InversionSolution, etc.)
    *.py           # Base types: File, Thing, Table, FileRelation, TaskTaskRelation
  data/            # Data access layer
    base_data.py   # BaseDynamoDBData: DynamoDB read/write, S3 fallback, ES indexing
    data_manager.py# DataManager singleton: entry point with .file, .thing, .table properties
    *_data.py      # FileData, ThingData, TableData, etc.
  dynamodb/
    models.py      # PynamoDB models: ToshiFileObject, ToshiThingObject, ToshiTableObject, ToshiIdentity
```

### Data Storage Model

Objects are categorised into three stores managed by PynamoDB models:
- **ToshiThingObject** — task/entity records (GeneralTask, RuptureGenerationTask, AutomationTask, etc.)
- **ToshiFileObject** — file records with S3 references (File, RuptureSet, InversionSolution variants, etc.)
- **ToshiTableObject** — tabular data
- **ToshiIdentity** — monotonic ID counter per object type

Every object has a `clazz_name` field in its JSON; `ThingData.from_json()` and `FileData.from_json()` use this to dynamically instantiate the correct Graphene class via `getattr(import_module('graphql_api.schema'), clazz_name)`. **All schema types used this way must be exported from `graphql_api/schema/__init__.py`.**

Objects are written to DynamoDB and simultaneously indexed in Elasticsearch. On read, DynamoDB is tried first; if not found, S3 is used as a legacy fallback.

### GraphQL Schema Pattern

Each domain type follows this pattern in `graphql_api/schema/custom/`:
1. **ObjectType** class with `class Meta: interfaces = (relay.Node, Thing|FileInterface)`
2. **CreateXxx(relay.ClientIDMutation)** with an `Input` class and `mutate_and_get_payload`
3. **UpdateXxx(relay.ClientIDMutation)** for mutable types

Mutations call `get_data_manager().thing.create(...)` or `.file.create(...)`, which handles ID allocation, DynamoDB write, and ES indexing transactionally.

### Key Interfaces
- `Thing` — base interface for task/entity types (stored in ToshiThingObject)
- `FileInterface` — base interface for file types (stored in ToshiFileObject)
- `PredecessorsInterface` — for types that track predecessor objects

### ID Scheme
Object IDs are auto-incremented integers (starting at `FIRST_DYNAMO_ID`, default 100000) with a 5-char random suffix appended (`append_uniq`). IDs are globally unique relay node IDs encoded as `base64(TypeName:id)`.

### Config Flags
All config is in `graphql_api/config.py` and loaded from `.env`:
- `TESTING=1` — disables real AWS calls; moto mocking is used
- `SLS_OFFLINE=1` — points to local DynamoDB (port 8000) and local S3 (port 4569)
- `DB_READ_ONLY=1` — prevents any writes
- `FIRST_DYNAMO_ID` — starting ID for new objects (0 for smoketests, 100000 for production)

### Testing Fixtures
Tests import `graphql_client` from `conftest.py`, which wraps the schema in `moto`'s `mock_aws` context, creates DynamoDB tables via `migrate()`, and creates an S3 bucket. Tests make GraphQL requests directly via `graphene.test.Client`.
