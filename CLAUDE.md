# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`nshm-toshi-api` is a GraphQL API (Strawberry + FastAPI, served via Mangum) deployed as an AWS Lambda function via the Serverless Framework. It serves as the object store for New Zealand NSHM (National Seismic Hazard Model) experiments and outputs — storing task metadata, file references, and computation results in DynamoDB + S3, with Elasticsearch for search.

## Commands

### Setup
```bash
uv sync        # Install Python dependencies
yarn install          # Install Node/Serverless dependencies (requires Node 22, yarn 2/berry)
yarn sls dynamodb install  # Install DynamoDB local plugin (Java required)
```

### Running Tests
```bash
uv run pytest                          # Run all tests
uv run pytest graphql_api/tests/test_auth.py  # Run a single test file
uv run pytest -k "test_name"           # Run tests matching a pattern
```

Tests use Docker testcontainers (DynamoDB Local + Elasticsearch 7.1.0) — the Docker daemon must be running. `graphql_api/tests/conftest.py` sets `TESTING=1` at module load so the `AuthExtension` short-circuits (see "Auth in tests" below).

### Linting & Formatting
```bash
uv run ruff format graphql_api         # Format code (120 char line length)
uv run ruff check graphql_api          # Lint
uv run ruff check --fix graphql_api    # Lint and auto-fix
```

### Local Development
```bash
yarn sls dynamodb start --stage local &
yarn sls s3 start &
uv run uvicorn graphql_api.app:app --reload   # FastAPI on http://localhost:8000/graphql
```
Requires `.env` with `SLS_OFFLINE=1`, `TESTING=0` (or `1` to bypass auth), `FIRST_DYNAMO_ID=0`.

Elasticsearch must also be running locally:
```bash
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.1.0
```

### Security Auditing
```bash
uv export --format requirements-txt --no-emit-project --output-file audit.txt
uv run pip-audit -r audit.txt -s pypi --require-hashes
```

## Architecture

### Layered Structure

```
graphql_api/
  app.py                 # FastAPI + Mangum entry point; `handler` is the Lambda entry
  schema.py              # Root Strawberry schema — Query + Mutation, AuthExtension wired
  auth.py                # AuthExtension: toshi/read + toshi/write scope enforcement
  models/                # Strawberry types — one file per GraphQL type
    _base/               # Storage-aligned types: thing, file, table, object_identity
    _interfaces/         # file_interface, inversion_solution_interface,
                         # predecessors_interface, predecessor
    _infra/              # common (scalars), page_info, _dispatch (clazz_name lookup),
                         # inversion_solution_union
    aggregate_inversion_solution.py, automation_task.py,
    general_task.py, inversion_solution.py, openquake_hazard_*,
    rupture_set.py, sms_file.py, strong_motion_station.py, ...   # Domain types
    relations.py         # FileRelation, TaskTaskRelation (uses strawberry.lazy for cycles)
  data/                  # Data access layer
    dynamo.py            # DynamoDB CRUD + scan + ES indexing
    s3.py                # S3 read fallback for legacy object IDs (< FIRST_DYNAMO_ID)
    search.py            # Elasticsearch search
    models.py            # Pydantic data models (per-domain *.Data classes)
    ids.py               # Global ID encode/decode + auto-increment IDs
  tests/                 # pytest suite, testcontainers-driven (DynamoDB Local + ES)
  tools/                 # SDL dump, schema parity check, runzi corpus refresh
```

`auth/` (top-level) holds the Lambda Authorizer (`auth/authorizer/`) and Cognito CLI tooling — not part of the GraphQL package.

### Data Storage Model

Three DynamoDB tables, modeled in `graphql_api/data/models.py`:
- **ToshiThingObject-{STAGE}** — task/entity records (GeneralTask, RuptureGenerationTask, AutomationTask, etc.)
- **ToshiFileObject-{STAGE}** — file records with S3 references (File, RuptureSet, InversionSolution variants, etc.)
- **ToshiTableObject-{STAGE}** — tabular data
- **ToshiIdentity-{STAGE}** — monotonic ID counter per object type

Every object has a `clazz_name` field in its JSON. The resolver path uses this to dispatch through `graphql_api/models/_dispatch.py` to the correct Strawberry type. **New domain types must be registered in `_dispatch.py` for `node()` / `nodes()` queries to find them.**

Objects are written to DynamoDB and simultaneously indexed in Elasticsearch. On read, DynamoDB is tried first; if not found, S3 is used as a legacy fallback (for IDs below `FIRST_DYNAMO_ID`).

### GraphQL Schema Pattern

Each domain type follows this pattern in `graphql_api/models/`:
1. **Strawberry type** decorated with `@strawberry.type`, implementing `relay.Node` and the relevant base interface (Thing or FileInterface).
2. **Input class** (`CreateXxxInput`) decorated with `@strawberry.input`.
3. **Payload class** (`CreateXxxPayload`) — the mutation return shape, matching the legacy Graphene `ClientIDMutation` shape exactly so existing clients work unchanged.
4. **Mutation function** (`mutate_create_xxx`) — called from the root mutation in `schema.py`.
5. **Resolver** (`resolve_xxxs`) for the connection field on Query.

Cross-type references use `strawberry.lazy("graphql_api.models.X")` string forward refs to break import cycles.

Mutations write through `graphql_api/data/dynamo.py` helpers (`create_thing`, `create_file`, etc.), which handle ID allocation, DynamoDB write, and ES indexing.

### Key Interfaces
- `Thing` — base interface for task/entity types (stored in ToshiThingObject)
- `FileInterface` — base interface for file types (stored in ToshiFileObject)
- `PredecessorsInterface` — for types that track predecessor objects

### ID Scheme
Object IDs are auto-incremented integers (starting at `FIRST_DYNAMO_ID`, default 100000) with a 5-char random suffix appended. IDs are exposed as Relay GlobalIDs (`base64(TypeName:id)`).

### Config

Most config comes from environment variables, read directly via `os.environ.get(...)` in the modules that need them (no central `config.py`).
- `TESTING=1` — bypasses `AuthExtension` (synthetic local-dev user with both scopes); set in `graphql_api/tests/conftest.py` for the suite.
- `SLS_OFFLINE=1` — also bypasses auth; set by `serverless-offline` for local dev.
- `DB_READ_ONLY=1` — set on the deployed `graphql` function in dev/prod; dropped on test (see `serverless.yml` serverlessIfElse).
- `FIRST_DYNAMO_ID` — starting ID for new objects (0 for smoketests, 100000 for production).
- `ES_ENDPOINT`, `ES_INDEX`, `GRAPHQL_PATH`, `S3_BUCKET_NAME` — wired in `serverless.yml`.

### Testing Fixtures
`graphql_api/tests/conftest.py` starts DynamoDB Local and Elasticsearch 7.1.0 via `testcontainers` (Docker required), creates fresh tables per test module, and yields a `gql_context` dict for `schema.execute_sync(..., context_value=...)` calls. There is no Flask `graphql_client` — tests drive Strawberry directly.

### Auth in tests
`graphql_api/auth.py`'s `AuthExtension` enforces `toshi/read` on every request and `toshi/write` on mutations. The conftest sets `TESTING=1`, which short-circuits the extension and attaches a synthetic `local-dev` user with both scopes — so existing tests run unchanged.

**Rule of thumb when adding scope-aware code**: any resolver or code path that reads `info.context["current_user"]` (scopes, userId, authMethod) to make a decision must have at least one test that disables the bypass and exercises real enforcement. See the `no_bypass` fixture and `_FakeRequest` pattern in `graphql_api/tests/test_auth.py`. Without it, the test silently passes under the synthetic user (which holds both scopes) and the real denial path is never exercised.
