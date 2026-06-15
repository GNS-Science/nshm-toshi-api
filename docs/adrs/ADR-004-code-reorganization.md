# ADR-004: Code Reorganization — Promote the Strawberry POC to `graphql_api/`

## Status

Proposed.

## Context

The Strawberry/FastAPI implementation lives at `spike/strawberry_poc/` —
the original feasibility-spike location, never moved as the work grew
into the substantive replacement for `graphql_api/`. As of #318 the
test-stage Lambda serves **all writes** through the POC at
`/test/graphql-v2`; the legacy Flask/Graphene stack at `/test/graphql`
is read-only.

Calling that code "spike" is now misleading: new contributors hit
`spike/strawberry_poc/` and reasonably assume it's experimental, and
tooling (CI working-directory, IDE config, pytest discovery) has to be
configured for a non-standard layout.

The cutover plan in #295 named this work as Phase 1 (reorg) and
Phase 2 (legacy pruning). Because all validation happens on the test
stage — there is no parallel testing in prod — the two phases
collapse into a single landing.

## Decision

### 1. Target location: `graphql_api/`

`spike/strawberry_poc/` → `graphql_api/`, the same path the legacy
code occupies today. Keeps the existing package name that downstream
tooling already knows, and gives the idiomatic
`from graphql_api.schema import schema` import path.

### 2. One PR, not three

Once the test-stage cutover is complete and the legacy `/graphql`
route is no longer load-bearing, a single PR:

- Deletes `graphql_api/` (the Flask/Graphene code) and the `app`
  Lambda from `serverless.yml`.
- Drops legacy deps (`graphene`, `flask`, `pynamodb`, `serverless-wsgi`)
  from `pyproject.toml`.
- `git mv spike/strawberry_poc/* graphql_api/` (preserving subdirs:
  `models/`, `data/`, `tests/`, `tools/`).
- Moves `strawberry_poc_handler.py` → `graphql_api/handler.py`.
- Renames the serverless function `strawberry-poc` → `graphql` and
  updates `package.include` accordingly. The URL path `/graphql-v2`
  is unchanged — path promotion is Phase 5.
- Replaces `spike.strawberry_poc.*` imports with `graphql_api.*`.
- Updates CI workflow `working-directory`, pyproject coverage source,
  CLAUDE.md, and ADR-002's audit footer paths.
- Consolidates `spike/strawberry_poc/pyproject.toml` into the top-level
  one.

Both `spike` and `poc` naming disappear from source, deploy config,
and Lambda function names in this PR.

The previous draft of this ADR split this into three PRs (prune,
rename, cleanup) on the assumption a side-by-side review window was
needed. Without parallel prod testing, the staging buys nothing: a
half-pruned or half-renamed tree is a broken intermediate, and the
diff is large but mechanical.

### 3. Use `git mv`

Preserves blame and `git log --follow`. Strawberry interface tracing
and ADR-002 back-references depend on it.

### 4. `spike/` stays for `spike/auth/`

`spike/auth/` is still active and out of scope here. Whether it
graduates to a top-level location is a separate decision.

## Consequences

### Positive

- One canonical location. Discoverable, idiomatic imports,
  no bespoke tooling config.
- Ends the "spike" misnomer that keeps surfacing in review.

### Negative

- Large diff (~30–50 files, mostly path substitutions). Mechanical;
  parity is verified by re-running the schema parity tool and the
  full test suite.
- Any out-of-tree consumer importing `spike.strawberry_poc.*` would
  break. None known — audit before merge.

## Prerequisites

1. Test-stage cutover complete: `/graphql` migrated off legacy.
2. mini Phase 4 testing concluded.

Both are tracked in #295.

## Related decisions

- [ADR-001](ADR-001-graphql-schema-evolution-strategy.md) — schema
  evolution.
- [ADR-002](ADR-002-schema-interface-hierarchy-and-input-naming.md) —
  the audit section there points at `spike/strawberry_poc/`; update
  in this PR.
