# ADR-004: Code Reorganization — Promote the Strawberry POC to a Top-Level Package

## Status

Proposed.

## Context

The Strawberry/FastAPI implementation lives at `spike/strawberry_poc/` —
the original "feasibility spike" location, never updated as the work
grew from a feasibility check into the substantive replacement for
`graphql_api/`. Today the directory contains:

- ~30 model files and a custom schema layer (`spike/strawberry_poc/models/`, `schema.py`)
- A complete data layer (`data/dynamo.py`, `data/s3.py`, `data/search.py`)
- 30+ test modules (~250+ passing tests on the test stage)
- ADR-002 interface implementations + the audit closures
- Its own `pyproject.toml`, `tox.ini`, and tooling under `tools/`

It is *de facto* the project's GraphQL API: as of #318 (mini Phase 4)
the test-stage Lambda `nzshm22-toshi-api-test-strawberry-poc` serves
**all writes** at `/test/graphql-v2`, with the legacy Flask/Graphene
stack at `/test/graphql` deliberately downgraded to read-only. Calling
that code "spike" is now misleading. New contributors hit
`spike/strawberry_poc/` and reasonably assume it is experimental. Git
history searches need to know to look there. Tooling (linters, IDEs,
test discovery) has to be configured for a non-standard layout.

The cutover plan in issue #295 names this work as **Phase 1 — Code
reorg** (POC → top-level), separately from **Phase 2 — Legacy
pruning** (delete `graphql_api/`). The two phases were proposed
separately because they answer different questions: "where does the
new code live?" and "when do we delete the old code?" — and the order
between them matters.

This ADR fixes both: the target location, and the sequencing.

### What this ADR is *not* about

- *Whether* to migrate from Graphene/Flask to Strawberry/FastAPI —
  that decision was made implicitly by the spike work shipping all the
  way through mini Phase 4. The migration is happening; this ADR is
  about how to land it.
- *When* to flip production — Phase 4 (traffic flip on prod) and Phase
  5 (path promotion) have their own ADRs to come.
- *The numbering drift in ADR-001 / ADR-002.* Both predict
  `ADR-003 = scalar policy`, but ADR-003 was actually used by
  chrisdicaprio for the Cognito permission model (good and useful
  work). Future scalar/deprecation/camelCase ADRs will land as
  ADR-005, ADR-006, ADR-007 in chronological order.

## Decision

### 1. Target location: `graphql_api/`

`spike/strawberry_poc/` → `graphql_api/`. The same path the legacy
code occupies today.

Alternatives considered:

| Option | Verdict | Why |
|---|---|---|
| **`graphql_api/`** (replace legacy) | ✅ adopt | Single canonical location; matches what new contributors expect; importable as `graphql_api.schema` (industry-norm shape) |
| `graphql/` (no `_api` suffix) | ❌ reject | Saves one suffix; loses continuity with the existing package name that downstream tooling (CI, IDE configs, GH search) already knows |
| `graphql_v2/` (versioned) | ❌ reject | "v2" is the path-versioning baggage we're explicitly removing in Phase 5 (see *ADR-002 §3a Ex-D* discussion of `/graphql-v2`). The same logic applies to the package name |
| `api/` (generic) | ❌ reject | Too generic; nothing in the name tells you it's GraphQL |
| Keep `spike/strawberry_poc/` | ❌ reject | "spike" semantically wrong; loses the discoverability win that motivated this ADR |

### 2. Sequence: legacy pruning happens **before** the rename

Phases 1 (reorg) and 2 (pruning) get coordinated into a single
sequence of three PRs:

1. **PR-A — Legacy retirement (Phase 2, blocking on cutover completion).**
   Delete `graphql_api/` (the Flask/Graphene code, ~12k LOC and ~178
   legacy tests). Drop the `app` Lambda from `serverless.yml`. Drop
   `serverless-wsgi`, `graphene`, `flask`, `pynamodb` from
   `pyproject.toml`. After this PR, the path `graphql_api/` is free.
   *Must wait until the live `/graphql` route has been migrated to the
   POC — see Phase 5 in #295.*

2. **PR-B — Reorg (Phase 1, immediately after PR-A merges).**
   `git mv spike/strawberry_poc/* graphql_api/` plus the
   sub-directories. Update internal imports (`spike.strawberry_poc.*` →
   `graphql_api.*`). Update the Lambda handler reference in
   `serverless.yml` (`strawberry_poc_handler.handler` →
   `graphql_api.handler.handler` or equivalent). Update the CI
   workflow's `working-directory` from `spike/strawberry_poc` to
   `graphql_api`. Update `pyproject.toml`'s test target and
   `tool.coverage.source` settings.

3. **PR-C — Cleanup (Phase 1 follow-up, low-priority).** Delete the
   now-empty `spike/` directory if no other spike work remains there
   (currently `spike/auth/` is still active — leave it alone in PR-B,
   handle in a separate decision). Update any remaining doc cross-
   references that pointed at `spike/strawberry_poc/` (CLAUDE.md,
   READMEs, ADR-002's audit footer, etc.).

### Why prune-first, not rename-first

Three options for the sequence were considered:

| Order | Verdict | Why |
|---|---|---|
| **Prune, then rename** (chosen) | ✅ adopt | Each PR is reviewable in isolation; no temporary "two implementations at top level" state; legacy `graphql_api/` becomes vacant cleanly, POC slides in |
| Rename POC to `graphql_api_v2/`, prune legacy, rename `_v2` → final name | ❌ reject | Three PRs instead of two; awkward intermediate state; lots of churn in import paths and tooling |
| Mega-PR: prune + rename in one swoop | ❌ reject | Diff would be enormous (delete 12k LOC, move 30+ files, fix all imports). Review-hostile and revert-hostile |

### 3. Tooling: `git mv` over `git rm` + `git add`

Use `git mv` (or rename detection via `-M` on the diff) so blame and
history survive the move. Strawberry interface tracing, ADR-002 audit
back-references, and `git log --follow` on individual files all
depend on this.

### 4. Test location: alongside source as a sibling

`graphql_api/tests/` — same convention as the current POC layout
(`spike/strawberry_poc/tests/`). The legacy code also used that path;
it's vacant once PR-A lands. Pytest convention allows either
side-by-side or top-level `tests/`; we keep side-by-side because (a)
it matches existing POC habit, (b) it makes `graphql_api/` a single
self-contained package.

### 5. Lambda handler entry point

The POC currently uses `strawberry_poc_handler.py` at the repo root
(per `spike/strawberry_poc/COVERAGE_GAPS.md`'s package include block).
After PR-B, it moves to `graphql_api/handler.py` and the serverless.yml
function block updates accordingly. No deploy-time URL change.

### 6. `pyproject.toml` consolidation

The POC has its own `pyproject.toml` at `spike/strawberry_poc/`. After
PR-B that file moves to `graphql_api/pyproject.toml`. The top-level
`pyproject.toml` was updated in #310 to include the POC's runtime
dependencies (`strawberry-graphql[fastapi]`, `mangum`, `pydantic`);
PR-A will additionally remove the legacy deps (`graphene`, `flask`,
`pynamodb`). The two `pyproject.toml`s coexist briefly; PR-B
reconciles into one top-level file.

## Consequences

### Positive

- **Discoverability**: new contributors find the code at the obvious
  path. `graphql_api/` is what the package is called, and it lives at
  the top level alongside `auth/`, `docs/`, etc.
- **Tooling alignment**: IDE jump-to-definition, `pytest tests/`,
  Codecov reports, sphinx autodoc (if/when added) — all stop needing
  bespoke configuration for an in-tree spike directory.
- **Import paths become idiomatic**: `from graphql_api.schema import schema`
  instead of `from spike.strawberry_poc.schema import schema`. Matches
  what clients writing custom test harnesses would expect.
- **Ends the "spike" misnomer**: removes a friction point in PR review
  ("wait, are we still calling this experimental?").

### Negative

- **One coordinated review window** during the PR-A → PR-B sequence
  where contributors stage work against both `spike/strawberry_poc/`
  and (after merge) `graphql_api/`. Mitigated by landing both PRs
  same-day where possible.
- **Internal-import churn**: every file under `spike/strawberry_poc/`
  that uses internal absolute imports needs updating. PR-B is
  predominantly `sed`-able but each test file's `from schema import schema`
  shorthand depends on `pythonpath` settings — those need to update too.
- **Out-of-tree consumers** (none known) that imported from
  `spike.strawberry_poc.*` would break. Audit before PR-B.

### Neutral

- **`spike/` directory remains** for as long as `spike/auth/` does. PR-B
  does not touch it. Whether `spike/auth/` graduates to top-level (with
  its own ADR) is out of scope here.

## Implementation plan for PR-B

Once PR-A has merged and `graphql_api/` is vacant:

1. `git mv spike/strawberry_poc/* graphql_api/`
   (preserve subdirectories — `models/`, `data/`, `tests/`, `tools/`)
2. Move `strawberry_poc_handler.py` → `graphql_api/handler.py`
3. Replace `from spike.strawberry_poc.X` and `from spike.strawberry_poc import X`
   with `from graphql_api.X` / `from graphql_api import X` across:
   - Source files under `graphql_api/`
   - The Lambda handler
   - Top-level pyproject.toml package config
   - CI workflow `working-directory`
4. Update `serverless.yml`:
   - `handler:` path
   - `package.include` (`spike/strawberry_poc/**` → `graphql_api/**`)
   - `package.exclude` (drop the now-irrelevant `spike/` exclude)
5. Consolidate `pyproject.toml`s into the top-level one; remove
   `spike/strawberry_poc/pyproject.toml`.
6. Update CLAUDE.md (its current spike-directory references) and any
   README that points at `spike/strawberry_poc/`.
7. Update `docs/adrs/ADR-002` "Post-implementation audit" section's
   path references for code-reorg accuracy.
8. Run the full suite under the new layout; confirm 250+ tests pass.
9. Re-run the schema parity tool — output should be byte-identical.

### Estimated size

PR-B is large in line count (many imports touched) but mechanical
(near-100% sed-style edits). Estimated 30–50 files touched, ~500
lines diff (mostly path substitutions).

## Why not now

Mini Phase 4 is currently in test, with chrisdicaprio exercising the
POC writes via runzi. Moving the source while that's in progress
would:

1. Disrupt his branch state if any local checkout is needed.
2. Add noise to subsequent CI runs (CI workflow path changes plus
   import-path churn make `gh run view` outputs less useful to him).
3. Block on test-stage rollback if any of his findings need a quick
   POC patch — the import paths would have just shifted.

Therefore PR-A and PR-B both wait for:

1. mini Phase 4 testing to conclude (chrisdicaprio's blessing).
2. The cutover decision to move `/graphql` from legacy to POC on test
   stage (which makes PR-A safe — legacy code can be deleted only
   after the live `/graphql` route stops pointing at it).

Once those two prerequisites are met, PR-A → PR-B can land back to
back, probably within the same day.

## Related decisions

- [ADR-001](ADR-001-graphql-schema-evolution-strategy.md) — schema
  evolution strategy. The reorg doesn't change schema semantics; it
  just moves where the schema-implementing code lives.
- [ADR-002](ADR-002-schema-interface-hierarchy-and-input-naming.md) —
  interface hierarchy & input naming. The "Post-implementation
  audit" section there has paths that point at `spike/strawberry_poc/`;
  those need updating in PR-B.
- (Future) ADR-005: Custom scalar policy.
- (Future) ADR-006: Deprecation logging and sunset policy — how we
  measure deprecated-field usage and when we remove (ADR-001 Phase 3).
- (Future) ADR-007: snake_case vs camelCase for client-facing fields
  — strategic call on whether to undertake the broader migration.
- (Future) ADR-NNN: `spike/auth/` graduation — whether the auth
  middleware moves to a top-level `auth/` location (note: the
  authorizer already lives at `auth/`; only `spike/auth/middleware.py`
  and friends are in spike).
