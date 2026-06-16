# Strawberry / FastAPI POC

A side-by-side spike in `spike/strawberry_poc/` that evaluates replacing the current
Graphene 3 / Flask / PynamoDB stack with Strawberry / FastAPI / boto3 while keeping
the existing DynamoDB tables and GraphQL API surface unchanged.

## What this is

The current production API (`graphql_api/`) has 44 schema types across 21 files,
written in Graphene 3 + Flask. It works but is verbose — every type requires a
`class Meta`, a separate `Connection`, and an `Input` inner class. PynamoDB adds
another abstraction layer for DynamoDB access.

This POC implements a representative slice of the same API using Strawberry
(the modern, type-hint-first GraphQL library that has largely displaced Graphene
in the Python community). The goal was not to rewrite everything — just to exercise
the hardest problems and produce concrete feasibility signals.

### Types implemented

| Type | Why it was chosen |
|------|-------------------|
| `GeneralTask` | Simplest Thing-table record; create + update mutations |
| `RuptureSet` | File-table record with a `produced_by` relation (union type stress-test) |
| `RuptureGenerationTask` | Stub; the union member that `produced_by` resolves to |
| `ToshiFile` | Base file type; covers File-table + relay Node pattern |

Together these exercise: relay Node + Connection, union types, both DynamoDB tables
(ToshiThingObject and ToshiFileObject), create/update mutations, and relay global IDs.

### Structure

```
spike/strawberry_poc/
  app.py               FastAPI + Mangum Lambda entry point
  schema.py            Root Query + Mutation (~80 lines vs 311 in the original)
  models/
    general_task.py    GeneralTask type, input types, resolvers
    rupture_set.py     RuptureSet + RuptureGenerationTask + union type
    file.py            ToshiFile type
    common.py          KeyValuePair, enums (TaskSubType, ModelType)
  data/
    dynamo.py          Thin boto3 wrapper: get/create/update/list for Thing + File tables
    ids.py             ToshiIdentity counter + append_uniq (same logic as base_data.py)
  tests/
    conftest.py        moto mock_aws fixtures (same pattern as graphql_api/tests/)
    test_general_task.py
    test_rupture_set.py
  pyproject.toml       Standalone deps: strawberry-graphql[fastapi], boto3, mangum
```

## Running the tests

```bash
cd spike/strawberry_poc
uv run pytest -v
```

All 44 tests run via `uv run pytest`. No manual service startup needed —
testcontainers pulls and starts `amazon/dynamodb-local` and
`elasticsearch:7.1.0` automatically via Docker.

### Docker-in-Docker constraint

All 44 passing tests require Docker (DynamoDB Local + Elasticsearch containers).
This is fine in CI (GitHub Actions `ubuntu-latest` runs on VMs, not containers)
but breaks in any environment that is itself a Docker container — e.g. the
`pyup`/security-patching tool.

**Workaround options:**

| Option | Notes |
|--------|-------|
| `pytest -m "not docker"` | Skip container-dependent tests; add `@pytest.mark.docker` to mark them. Fast, portable, no Docker needed. Suitable for dep-bump regression checks. |
| Socket mount | Pass `-v /var/run/docker.sock:/var/run/docker.sock` to the outer container. Spawned containers become siblings on the host daemon. Works, but gives full Docker access — a concern for a security tool. |
| Testcontainers Cloud | Docker's commercial product (free tier for OSS). Library talks to a remote Docker host; no local socket needed. Requires `TESTCONTAINERS_CLOUD_TOKEN`. |

Recommended: use `pytest -m "not docker"` in containerised environments and
let CI run the full suite.

The tests use `moto` to mock DynamoDB and call `schema.execute_sync()` directly —
no HTTP server required, same pattern as the existing test suite.

## What the tests verify

### `test_general_task.py`

| Test | What it confirms |
|------|-----------------|
| `test_create_returns_id` | relay GlobalID is `base64("GeneralTask:<raw_id>")` — **identical to Graphene encoding** |
| `test_create_fields` | All scalar fields (str, int, enum, list of KV pairs) round-trip cleanly |
| `test_swept_arguments` | Computed fields (`@strawberry.field`) work alongside stored fields |
| `test_list_general_tasks` | `relay.ListConnection` + boto3 scan return correct edges |
| `test_node_lookup` | `node(id: ...)` interface dispatches to the correct type via `resolve_node` |
| `test_update_general_task` | Partial-update mutation preserves unset fields; returns updated values |
| `test_update_preserves_id` | Update does not change the relay global ID |

### `test_rupture_set.py`

| Test | What it confirms |
|------|-----------------|
| `test_rupture_set_id_encoding` | File-table IDs encode correctly (`RuptureSet:...`) |
| `test_rupture_gen_task_id_encoding` | Thing-table IDs encode correctly (`RuptureGenerationTask:...`) |
| `test_rupture_set_fields` | File fields (md5, size, fault_models, metrics) round-trip |
| `test_produced_by_resolved` | Lazy `produced_by` resolver crosses from File table → Thing table |
| `test_list_rupture_sets` | File-table list query works independently of Thing-table list |
| `test_node_lookup` | `node(id: ...)` resolves a RuptureSet and eagerly loads `produced_by` |
| `test_relay_ids_are_different_types` | File and Thing objects have distinct type prefixes in their IDs |

## Feasibility signals

| Signal | Result | Notes |
|--------|--------|-------|
| relay GlobalID encoding | **Compatible with Graphene** | Both use `base64("TypeName:id")` — existing client code and stored IDs work unchanged |
| `relay.NodeID` pattern | **Clean** | `pk: relay.NodeID[str]` on each type; strawberry handles GlobalID wrapping automatically |
| `relay.ListConnection` | **Works out of the box** | No custom `Connection` class needed (removes ~1/3 of Graphene boilerplate) |
| Union types | **Clean** | `strawberry.Private` + lazy `@strawberry.field` for `produced_by`; no `is_type_of` hacks |
| FastAPI + Mangum | **Drop-in** | `handler = Mangum(app)` replaces `serverless-wsgi`; same Lambda handler interface |
| Schema verbosity | **~3× reduction** | `schema.py` is 80 lines; Graphene equivalent is 311 lines for same surface area |
| moto test pattern | **Reusable** | `conftest.py` is identical in structure to `graphql_api/tests/conftest.py` |
| DynamoDB data migration | **Not required** | Same tables, same JSON layout (`object_content` column) — boto3 reads existing data |

**Version note:** strawberry ≥ 0.300 requires `pk: relay.NodeID[str]` on every
`relay.Node` subclass. Earlier tutorials and docs show manual `relay.GlobalID(...)` construction
— that pattern no longer works. Tested against **0.314.3**.

## Pydantic integration experiment

The POC uses Pydantic v2 as a data validation layer between DynamoDB raw dicts and Strawberry
types. Two integration depths were evaluated:

### Phase 1 — Pydantic as a validation layer (adopted)

`data/models.py` defines one `BaseModel` per DynamoDB type. Each Strawberry type's `from_dict`
calls `XxxData.model_validate(raw_dict)` for type-safe field access and early validation.
The Pydantic models and Strawberry types are separate; `from_dict` bridges them.

This is the approach in use. It is straightforward, predictable, and the tests pass unchanged.

### Option C — `strawberry.experimental.pydantic` (evaluated, not adopted)

`@strawberry.experimental.pydantic.type(model=...)` can compose with `relay.Node`. The recipe
that works:

```python
@strawberry.experimental.pydantic.type(model=GeneralTaskData)
class GeneralTask(relay.Node):
    pk: relay.NodeID[str]          # not in Pydantic model → passed via extra={}
    title: strawberry.auto         # auto-mapped from Pydantic field
    subtask_type: strawberry.auto  # works only if Pydantic field type IS the enum
    argument_lists: strawberry.auto  # works if nested type is also pydantic-experimental
    files_raw: strawberry.Private[list]
```

`from_pydantic(model, extra={"pk": ..., "files_raw": ...})` handles conversion. `resolve_node`,
`@strawberry.field`, and `strawberry.Private` all survive the decorator. `relay.ListConnection`
generates `Connection`/`Edge` types correctly.

**Why not adopted:**

1. **All-or-nothing coupling.** Every nested type (`KeyValuePair`, `KeyValueListPair`) must also
   be pydantic-experimental, and `data/models.py` must use enum types (not `str`) so Pydantic
   coerces values before `from_pydantic` sees them. Any type that is not pydantic-experimental
   causes `from_pydantic` to fail with a confusing `AttributeError`.

2. **Custom classmethods are dropped.** The decorator rebuilds the class and strips any classmethod
   not part of the relay interface (e.g. `from_dict`). These must become module-level functions.

3. **Experimental label is load-bearing.** Strawberry has changed this API across minor versions.
   The `strawberry.auto` annotation and `from_pydantic` signature have both shifted in 0.2xx→0.3xx.

Revisit if Strawberry stabilises the pydantic experimental API in a future major release.

## What remains for a full migration

The POC covers the hard architectural problems. A full migration would be a significant
but well-understood effort.

### Schema types (44 total, 3 implemented here)

The remaining ~41 types follow the same patterns shown here:

- **Thing types** (stored in `ToshiThingObject`): `AutomationTask`, `RuptureGenerationTask`
  (full, not stub), `InversionSolution`, `TimeDependentInversionSolution`, `OpenquakeHazardTask`,
  `OpenquakeHazardSolution`, `AggregateInversionSolution`, `ScaledInversionSolution`,
  `SubductionInversionSolution`, and ~15 more.
- **File types** (stored in `ToshiFileObject`): `InversionSolutionFile`,
  `OpenquakeHazardTaskResult`, `GrandInversionStats`, `LabelledTableRelation`, and ~10 more.
- **Table types** (stored in `ToshiTableObject`): `StrongMotionStation`, `GroundMotionTable`,
  `GriddedHazard`, and others.
- **Relation types**: `FileRelation`, `TaskTaskRelation`, `PredecessorsInterface` —
  these link objects together and need the same lazy-resolver pattern as `produced_by`.

### Data layer

- `data/dynamo.py` needs a `_table_table` path for `ToshiTableObject` (trivial copy of
  the Thing/File equivalents).
- S3 fallback read (legacy data not yet in DynamoDB) — currently omitted. The existing
  `base_data.py` S3 fallback logic can be ported as a decorator or fallback in `get_thing` /
  `get_file`.
- Elasticsearch indexing on write — currently omitted. The existing `ThingData.index_search()`
  / `FileData.index_search()` calls can be added as post-write hooks in `create_thing` and
  `create_file`.
- **ID allocation transaction guard** — the POC's `create_thing` / `create_file` increment
  the ToshiIdentity counter and save the object as two separate DynamoDB calls. The production
  code (`base_data._write_object`, line 350) does both atomically via PynamoDB `TransactWrite`,
  with an exponential-backoff retry on contention. Three things to restore:
  1. Replace the two-call pattern with a single `boto3` `transact_write_items` that increments
     the counter and saves the object together
  2. Add a `backoff` retry on `ClientError` / `TransactionConflict` error code
  3. Re-add the pre-write consistency check (`identity.object_id == expected_id`) that raises
     `DynamoWriteConsistencyError` on mismatch

### Auth

The Lambda Authorizer (`spike/auth/authorizer/handler.py`) is already decoupled from the
web framework — it runs at API Gateway before the request reaches the app. No changes needed.

For request-level scope enforcement (read vs write), the `spike/auth/middleware.py`
Flask `before_request` hook needs porting to a FastAPI dependency:

```python
# Strawberry equivalent of the Flask middleware
async def require_auth(info: Info) -> None:
    request = info.context["request"]
    scopes = request.state.authorizer.get("scopes", [])
    if "toshi/write" not in scopes:
        raise PermissionError("write scope required")
```

### Testing

- The existing 11,796-line test suite uses `graphene.test.Client` and Graphene-specific
  query patterns. Most query strings are reusable (same GraphQL shape), but the client
  wrapper and assertion helpers need updating to `schema.execute_sync()`.
- With module-scoped moto fixtures (as used here), a full suite run should be comparable
  in speed to the current suite.

### Deployment

- Replace `serverless-wsgi` with `mangum` in `serverless.yml` (handler path changes from
  `graphql_api/wsgi_handler.handler` to `app.handler`).
- `requirements.txt` / `pyproject.toml` gains `strawberry-graphql[fastapi]`, `mangum`;
  loses `Flask`, `graphene`, `PynamoDB`.
- Cold start impact is worth measuring — FastAPI startup is heavier than Flask, but Mangum
  adds negligible overhead. Strawberry schema compilation happens at import time (same as
  Graphene).
