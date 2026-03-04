# Codebase Cleanup Plan

## Overview

The codebase is well-structured at its core but has accumulated technical debt across tests, dependencies, docs, and missing data migration tooling. This plan is organized into 5 workstreams with clear phases.

---

## Workstream 1: Test Cleanup & Standardization

### Current state
- 53 test files (~68 total with support files)
- 3 `conftest.py` files (root, `rupture_set/`, `swept_arguments/`)
- Duplicate test implementations: `legacy/` vs `simpler_relationships/` (3 pairs)
- 11 bug-specific regression test files (`test_*_bugfix_*.py`)
- Mixed moto patterns: some `@mock_aws` decorator, some context manager `with mock_aws()`
- `module` and `session` scope fixtures causing subtle test isolation issues

### Target state
- Single consistent pattern: `pytest` + `conftest.py` fixtures + `moto.mock_aws` context manager
- No duplicate test implementations
- Bug regression tests folded into relevant domain test files (with `# regression: #issue` comments)
- Clear fixture hierarchy: global → domain → test-level

### Steps

**1.1 Audit and remove legacy/ tests**
- Validate `simpler_relationships/` tests cover everything in `legacy/`
- Delete `legacy/test_automation_task_related_solution.py`
- Delete `legacy/test_inversion_solution_file_migration_bug.py`
- Delete `legacy/test_rupture_generation_related_files.py`
- Delete `legacy/` directory if empty

**1.2 Standardise moto usage**
- Replace all `@mock_aws` decorator usage with `mock_aws()` context manager in fixtures
- Ensure all tests get a fresh `mock_aws` context (avoid session-scoped AWS state leaking)
- Add `autouse=True` fixture in root `conftest.py` that wraps each test in `mock_aws()`

**1.3 Consolidate conftest.py**
- Promote shared fixtures from `rupture_set/conftest.py` and `swept_arguments/conftest.py` to root or dedicated `graphql_api/tests/conftest_domain.py`
- Document fixture scope decisions (why session vs function scope)

**1.4 Rename and reorganise bug regression tests**
- Move `test_*bugfix_159*` etc. into their domain test file with `@pytest.mark.regression` marker
- Remove standalone bugfix test files once folded in

**1.5 Enforce pattern via pytest config**
- Add `pytest.ini` markers: `regression`, `integration`, `unit`
- Add `filterwarnings` to surface deprecation warnings from graphene/pynamodb

---

## Workstream 2: Architecture Cleanup & Stale Feature Removal

### Current state
- 17 TODO/FIXME comments (4 in `base_data.py` core)
- `graphql-server==3.0.0b7` (beta pinned)
- Duplicate `pyyaml` entry in `pyproject.toml`
- `black` targets `py39/py310` but project requires Python 3.12
- Commented-out code in `api.py` and `serverless.yml`
- `automation_task_base.py` status unclear (in `__pycache__` but not source)
- Spike auth code in `spike/` not integrated

### Steps

**2.1 Resolve all TODO/FIXME comments**
- `base_data.py` (4): review each — document decision or implement fix
- `schema/file.py`, `automation_task.py`, `inversion_solution.py` (3): same
- Test TODOs (10): either implement or delete dead test stubs

**2.2 pyproject.toml cleanup**
- Remove duplicate `pyyaml` entry
- Upgrade `graphql-server` from `3.0.0b7` → latest stable (test first)
- Update `black` targets to `['py312']`
- Review `requests-mock` upper bound — relax if safe

**2.3 Remove dead code**
- Remove `# from flask_graphql import GraphQLView` from `api.py`
- Clean up `serverless.yml` commented-out authorizer blocks (or replace with clear `# TODO: enable after auth spike merges`)
- Verify `automation_task_base.py` — if unused, delete
- Audit `schema/__init__.py` exports: remove any types no longer referenced by `from_json()`

**2.4 Resolve TaskSubType duplicate**
- Fix `common.py` line 58 `# duplicate??` comment on `OPENQUAKE_HAZARD` enum value
- Check all usages and consolidate

**2.5 Finalize or shelve spike/auth**
- Decision required: merge spike auth to main or move to separate branch
- If shelving: remove `try-import` from `api.py`, remove `PyJWT` from pyproject.toml
- If merging: write a proper integration plan (separate PR)

**2.6 Type hint expansion**
- Add mypy `strict = false` baseline config to `pyproject.toml`
- Add type hints to `data/base_data.py` and `data/data_manager.py` (core layer)
- Don't force schema types — graphene typing is awkward; focus on data layer

---

## Workstream 3: Data Migration — Old → New Datastore

### Current state
- No explicit migration versioning system
- `migrate()` only creates tables if absent; no schema evolution
- DynamoDB stores raw JSON with `clazz_name` field; S3 used as fallback for legacy records
- No tooling to bulk-inspect or repair stored records

### Steps

**3.1 Audit existing data**
- Write a `scripts/audit_datastore.py` that scans all three tables (ToshiThingObject, ToshiFileObject, ToshiTableObject)
- Reports: count per `clazz_name`, identifies records with missing/unexpected fields, finds S3-only fallback records
- Output: JSON report + summary CSV

**3.2 Formalise migration versioning**
- Add a `schema_version` field to PynamoDB models (nullable, default `null` = v0)
- Create `graphql_api/migrations/` directory with numbered migration modules:
  ```
  graphql_api/migrations/
    __init__.py
    migration_001_add_schema_version.py
    migration_002_backfill_predecessor_interface.py
    ...
  ```
- Update `migrate()` in `api.py` to run pending migrations in order

**3.3 Migrate S3-fallback records into DynamoDB**
- Write `scripts/migrate_s3_legacy.py`:
  - Iterates all object IDs (from ToshiIdentity)
  - For each: attempts DynamoDB read; if miss, reads from S3, re-writes to DynamoDB
  - Dry-run mode (`--dry-run`) vs live mode
  - Progress bar + error log

**3.4 Backfill production data**
- Run `audit_datastore.py` against staging + production
- For each identified gap, write a targeted backfill script
- All scripts: idempotent, dry-run first, log all changes to a local JSONL file

---

## Workstream 4: Schema Migration Tooling

### Current state
- When a schema type gains/loses fields, existing DynamoDB records silently have wrong shape
- No tooling to detect or repair field-level mismatches
- `from_json()` pattern is dynamic but fragile — unknown `clazz_name` raises `AttributeError`

### Steps

**4.1 Schema diff detector**
- Write `scripts/schema_diff.py`:
  - Reads live DynamoDB records for each `clazz_name`
  - Compares stored JSON keys against current Graphene field definitions
  - Reports: missing fields, unexpected fields, type mismatches (where checkable)

**4.2 Field migration helper**
- Write `scripts/field_migrate.py` with a simple DSL:
  ```python
  # Example: rename a field across all RuptureSet records
  migrate_field(
      clazz_name="RuptureSet",
      old_field="produced_by_id",
      new_field="rupture_generation_task_id",
      dry_run=True
  )
  ```
- Handles: rename, add-with-default, remove, type-coerce
- All operations are logged to `migration_log.jsonl` and are idempotent

**4.3 Safe from_json() fallback**
- Update `from_json()` in `thing_data.py` and `file_data.py` to handle unknown `clazz_name` gracefully
- Unknown types: return a `UnknownObject` stub type rather than raising `AttributeError`
- Log unknown type encounters to CloudWatch

**4.4 Integration with migrations system**
- Schema migrations (Workstream 3) use field migration helpers internally
- Each migration module is testable in isolation (with moto)

---

## Workstream 5: Documentation (MkDocs)

### Current state
- `README.md` covers setup/run/test basics
- `CLAUDE.md` covers architecture for Claude
- Demo slides (not browseable as docs)
- No API schema docs, no data model diagrams, no developer guides

### Steps

**5.1 Install and configure MkDocs**
- Add `mkdocs`, `mkdocs-material`, `mkdocs-gen-files` to dev deps
- Create `mkdocs.yml` at project root
- Structure:
  ```
  docs/
    index.md             ← project overview (from README)
    architecture.md      ← layered architecture, data model
    schema/
      types.md           ← all GraphQL types, auto-generated from introspection
      queries.md         ← example queries
      mutations.md       ← example mutations
    data/
      storage_model.md   ← DynamoDB table design, S3 fallback
      migrations.md      ← how migrations work, writing new ones
    development/
      setup.md           ← local dev setup
      testing.md         ← test patterns, fixtures, moto
      contributing.md    ← PR checklist, code style
    operations/
      deployment.md      ← Serverless deploy, env vars
      monitoring.md      ← CloudWatch, Elasticsearch
      auth.md            ← current x-api-key + planned JWT auth
  ```

**5.2 Auto-generate GraphQL schema docs**
- Add `scripts/export_schema.py` that runs GraphQL introspection and writes `schema.graphql`
- Use `mkdocs-gen-files` to include it in the built docs
- Add to CI: fail if `schema.graphql` is stale

**5.3 Architecture diagrams**
- Add Mermaid diagrams (supported by mkdocs-material) for:
  - Layered architecture (Flask → Graphene → DataManager → PynamoDB → DynamoDB/S3/ES)
  - Data flow for a typical mutation
  - Object type hierarchy (Thing / FileInterface / TableObject)

**5.4 CI integration**
- Add `mkdocs build --strict` to CI pipeline
- Deploy docs to GitHub Pages on merge to main

---

## Sequencing & Dependencies

```
Phase 1 (foundation):
  WS1: 1.1 remove legacy tests
  WS2: 2.2 pyproject cleanup, 2.3 dead code removal
  WS5: 5.1 MkDocs install

Phase 2 (data safety — do before any schema changes):
  WS3: 3.1 audit_datastore.py
  WS3: 3.2 migration versioning
  WS4: 4.1 schema_diff.py

Phase 3 (test standardisation):
  WS1: 1.2–1.5 moto/conftest/marker cleanup

Phase 4 (migration execution):
  WS3: 3.3–3.4 S3 backfill + production migration
  WS4: 4.2–4.3 field migration helpers + safe from_json()

Phase 5 (polish):
  WS2: 2.1 TODO resolution, 2.5 spike auth decision
  WS5: 5.2–5.4 auto-generated docs, diagrams, CI
```

---

## Rough Effort Estimate

| Workstream | Effort |
|------------|--------|
| WS1 Test cleanup | ~3–4 days |
| WS2 Architecture cleanup | ~2–3 days |
| WS3 Data migration | ~3–5 days (audit + scripts + run) |
| WS4 Schema migration tooling | ~2–3 days |
| WS5 MkDocs | ~2–3 days |
| **Total** | **~12–18 days** |

This is best done as a dedicated cleanup sprint before any new feature work.
