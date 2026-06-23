# Graphene → Strawberry Migration Runbook

**Reference migration:** `nshm-toshi-api` (Graphene 3 / Flask / serverless-wsgi → Strawberry / FastAPI / Mangum), completed 2026-06.
**Applies to:** `kororaa-graphql-api`, `nshm-hazard-graphql-api`, `nshm-model-graphql-api`, `solvis-graphql-api`.

---

## TL;DR

- The biggest cost is **not** the Graphene→Strawberry code conversion — it's deploy/CI/deps hygiene around the rewrite. Plan for it explicitly.
- Migrate **smallest-first** (`nshm-model-graphql-api` is the pilot). Treat the pilot as the runbook's regression test — fold every surprise back into this doc.
- Existing `x-api-key` auth must keep working unchanged. The `LEGACY_API_KEY` resolution chain in `serverless.yml` is the contract.

## Recommended sequencing

1. **`nshm-model-graphql-api`** — pilot. ~7 .py files, zip Lambda, no DynamoDB writes, no auth. Use to harden the runbook.
2. **`kororaa-graphql-api`** — zip Lambda, read-only boto3 to external prod tables. Same shape as Model, slightly bigger.
3. **`nshm-hazard-graphql-api`** — container Lambda (Dockerfile/ECR). Mangum replaces the existing serverless-wsgi/ECR `handler.py` workaround.
4. **`solvis-graphql-api`** — container Lambda + **PynamoDB** ORM. Biggest delta from toshi-api. Save for last so the runbook is fully battle-tested.

## How to use this doc

- **End-to-end migrator?** Read linearly. Each phase has a "🚧 Traps" box at its end — those are the things that bit us in toshi-api.
- **Already know Strawberry, just want to skip the landmines?** Read only the **🚧 Traps** boxes, **Phase 4** (deploy/CI/deps — the densest), and the **Traps index** in Appendix C.
- **About to start a specific sibling API?** Read the front matter, the relevant **per-API addendum**, and Phase 4.
- **DevOps reader without Python background?** Phase 2 (schema migration) is app-code territory — skim it for the trap boxes and hand the rest to whoever's doing the Python work. Phase 4 is your home.

## Prerequisites

- AWS access for the target stage (test first, then prod). IAM role assumable by GH Actions; `gh secret list --env AWS_TEST` and `--env AWS_PROD` to confirm wired secrets
- Docker daemon running (for `testcontainers`; also for container-Lambda APIs at build time)
- Node 22 + Yarn 4 (Berry). `corepack enable` before any `yarn install`
- `uv` installed (`brew install uv` or equivalent)
- Local Java only if the target API uses DynamoDB Local in tests (toshi-api does; check `tests/conftest.py` of the target sibling)

---

## Phase 0 — Pre-flight

### Goals
Capture the current behavioural contract so any regression during migration is caught early.

### Steps

1. **Baseline the legacy SDL.** Dump the current Graphene schema to a file checked into the repo:
   ```python
   # <pkg>/tools/dump_legacy_sdl.py  (e.g. graphql_api/tools/dump_legacy_sdl.py for toshi-api)
   from <pkg>.schema import schema  # graphene schema
   print(str(schema))
   ```
   ```bash
   uv run python -m <pkg>.tools.dump_legacy_sdl > schema.legacy.graphql
   git add schema.legacy.graphql && git commit -m "chore: baseline SDL for migration parity"
   ```
   This file is the parity target. Anything removed from the new SDL that isn't marked `@deprecated` is a breakage.

2. **Vendor a client query corpus.** Collect real production queries — from `runzi`, the web frontends, any internal scripts — into the repo as a fixture set:
   - See `graphql_api/tools/refresh_runzi_corpus.py` in toshi-api for the pattern.
   - One file per client; each query labelled with the calling component.
   - Vendor real query text, NOT live-fetched at test time — live-fetching introduces a deploy-time dependency that broke us once ([PR #325](https://github.com/GNS-Science/nshm-toshi-api/pull/325)).
   - Wire these into a CI job that replays them against the test-stage deploy.

3. **Inventory the current `serverless.yml`.** Record in a markdown scratchpad:
   - All stages (`dev`/`test`/`prod`/`local`)
   - Current `memorySize`, `timeout`, `runtime`
   - Plugin list (verbatim)
   - Custom resources (DynamoDB tables, S3 buckets, ES domains)
   - All env vars under `provider.environment`
   - All `iamRoleStatements`

4. **Inventory secrets per environment:**
   ```bash
   gh secret list                            # repo-level (NOT environment secrets — common mistake)
   gh secret list --env AWS_TEST
   gh secret list --env AWS_PROD
   ```
   Document the resolution chain for `LEGACY_API_KEY` / `x-api-key` — this contract must survive the migration.

### 🚧 Traps

- **SDL parity ≠ runtime parity.** Tools like `graphql-inspector diff` only compare types and fields. They miss: input field defaults, `@deprecated` directives (and the human reason text), behavioural changes inside resolvers (e.g. legacy returning `null` vs new raising). The query corpus catches the runtime gap.
- **Vendor the client queries — don't fetch them from the client at test time.** "Vendoring" means copying the client's query files into this repo (e.g. `tests/fixtures/runzi/*.graphql`) and committing them. The queries become a snapshot you control: CI runs against the same input every time, `git log` shows when they changed, and refreshing them is an explicit PR.

---

## Phase 1 — Project bootstrap (zip Lambda baseline)

### Goals
Stand up the new Strawberry/FastAPI scaffold alongside (or replacing) the legacy app, before touching any GraphQL types.

### Steps

1. **Consolidate Python deps under `uv`.** Drop `poetry`. The dockerbash `poetry2uv` skill automates this end-to-end — the poetry→uv conversion, the npm age-gate setup, documentation updates, and the move to `ruff`. Run it first; the steps below are then a verification checklist rather than manual work:
   - Delete `poetry.lock`, fold any `setup.cfg` settings into `pyproject.toml`
   - Generate `uv.lock`: `uv lock`
   - Sync: `uv sync`
   - All commands now `uv run <tool>` instead of `poetry run <tool>`
   - For security auditing: `uv export --format requirements-txt --no-emit-project --output-file audit.txt && uv run pip-audit -r audit.txt -s pypi`

2. **Add new runtime deps** to `pyproject.toml`:
   ```toml
   dependencies = [
     "strawberry-graphql>=0.243",  # floor: strawberry.field deprecation_reason on input fields
     "fastapi>=0.115",
     "mangum>=0.18",
     "pydantic>=2.0",
     # ... existing data-layer deps (boto3 etc.)
   ]

   [dependency-groups]
   dev = [
     "httpx>=0.27",
     "testcontainers>=4.0",
     "pytest>=8",
     "ruff>=0.6",
     # ...
   ]
   ```

3. **Create the FastAPI/Mangum entry point** at `<pkg>/app.py`:
   ```python
   from fastapi import FastAPI
   from mangum import Mangum
   from strawberry.fastapi import GraphQLRouter
   from <pkg>.schema import schema

   app = FastAPI()
   app.include_router(GraphQLRouter(schema, context_getter=...), prefix="/graphql")
   handler = Mangum(app)
   ```
   See `graphql_api/app.py` in toshi-api for the full version with context wiring.

4. **Create the schema entry** at `<pkg>/schema.py`:
   ```python
   import strawberry
   from strawberry import Schema
   from strawberry.schema.config import StrawberryConfig

   schema = Schema(
       query=Query,
       mutation=Mutation,
       extensions=[],  # AuthExtension wired here later if/when auth is added
       config=StrawberryConfig(auto_camel_case=False),  # ← required for legacy parity
   )
   ```

5. **Swap `serverless.yml`:**
   - Remove `serverless-wsgi` from `plugins:`
   - Remove the `custom.wsgi` block
   - Rename the function's `handler:` from `wsgi_handler.handler` to `<pkg>.app.handler`
   - Function memory: don't drop hard. Halve from the legacy value, monitor CloudWatch (see Phase 4 trap).

6. **Adopt the ruff/mypy config** (copy from toshi-api `pyproject.toml`):
   ```toml
   [tool.ruff]
   line-length = 120
   [tool.ruff.lint]
   select = ["E", "F", "I", "B", "UP", "G004", "PLC0415"]
   [tool.ruff.lint.per-file-ignores]
   "__init__.py" = ["F401"]
   "<pkg>/models/*.py" = ["F821"]      # strawberry.lazy forward refs
   "<pkg>/tests/**" = ["E501", "PLC0415"]
   ```

7. **Verify boot.** `uv run uvicorn <pkg>.app:app --reload` should serve `/graphql` and respond to `{ __typename }`.

### 🚧 Traps

- **Lint-config consolidation tightens previously-passing legacy code.** Switching to the strict ruff config above will fail on auth/ or other adjacent packages that the legacy ruleset never touched. Add per-file-ignores for those packages **before** the first PR ships, so the bootstrap PR's CI stays green (see toshi-api PR #338 — 89 ruff errors at first CI run).
- **`auto_camel_case=False` is mandatory** if your legacy schema uses snake_case field names. Strawberry's default flips to camelCase and breaks every existing client.

---

## Phase 2 — Schema migration

### Goals
Convert Graphene types to Strawberry types one domain at a time, keeping SDL parity throughout.

### Per-type pattern

For each domain type (`Foo`):

```python
# <pkg>/models/foo.py
import strawberry
from strawberry import relay

@strawberry.type
class Foo(relay.Node, FooInterface):
    pk: relay.NodeID[str]
    name: str | None = None
    # ... fields

    @classmethod
    def resolve_node(cls, node_id, *, info, **kwargs):
        data = get_thing(info.context["dynamodb"], node_id)
        return cls.from_dict(data) if data else None

    @classmethod
    def from_dict(cls, data: dict) -> "Foo":
        d = FooData.model_validate(data)
        return cls(pk=d.object_id, name=d.name, ...)


@strawberry.input
class CreateFooInput:
    name: str
    client_mutation_id: str | None = client_mutation_id_input_field()


@strawberry.type
class CreateFooPayload:
    foo: Foo | None
    client_mutation_id: str | None  # match legacy Graphene ClientIDMutation shape


def mutate_create_foo(info, input: CreateFooInput) -> CreateFooPayload:
    ...


def resolve_foos(info) -> Iterable[Foo]:
    ...
```

Wire `mutate_create_foo` and `resolve_foos` into the root `Mutation` / `Query` in `<pkg>/schema.py`.

### Patterns to use

- **Cycle-breaking:** `Annotated["Bar", strawberry.lazy("path.to.bar")]` for forward refs between types.
- **Runtime dispatch (conditional):** only needed if your API has polymorphic node lookup by a stored `clazz_name` (typical when one DynamoDB table holds multiple GraphQL types). Build a dispatch table (see toshi-api `graphql_api/models/_infra/_dispatch.py`). **Every new domain type must be registered here** or `node()` returns `None` for it. Models / Kororaa likely don't need this; Solvis / Hazard might.
- **Layered models** (recommended for any package with >10 types):
  - `<pkg>/models/_base/` — storage-aligned shared types (e.g. `thing`, `file`, `table`)
  - `<pkg>/models/_interfaces/` — GraphQL interfaces shared by domain types
  - `<pkg>/models/_infra/` — scalars, common enums, dispatch table, unions
  - `<pkg>/models/<domain>.py` — flat domain types
  - See toshi-api `graphql_api/models/` for the reference.
- **Pydantic v2 in the data layer:** keep DynamoDB shapes in `<pkg>/data/models.py` as `pydantic.BaseModel` classes (e.g. `FooData`), separate from the Strawberry `Foo`. `from_dict` does the validation + projection. This separation makes data migrations isolated from schema migrations.
- **PEP 695 generics** for utility functions: `def _try_enum[E: enum.Enum](enum_cls: type[E], value: str | None) -> E | None:` (ruff `UP047` enforces this).

### Deprecated fields — non-negotiable

```python
# Output field — works on both sides:
@strawberry.field(deprecation_reason="We no longer store this value.")
def config(self, info) -> Foo | None: ...

# Input field — MUST use strawberry.field, NOT strawberry.argument:
config: strawberry.ID | None = strawberry.field(
    default=None,
    deprecation_reason="We no longer store this config",
)
```

`strawberry.argument(deprecation_reason=...)` does **not** emit `@deprecated` on input fields. Use `strawberry.field` as shown.

### 🚧 Traps (the big one)

- **String module paths get missed by anchored regex.** Any of:
  - `strawberry.lazy("path.to.module")`
  - `importlib.import_module("path.to.module")`
  - `unittest.mock.patch("path.to.module.attr")`

  All hold module paths as strings. A `sed -E '^from data\.X'` will not touch them. Use an AST-aware refactor tool (e.g. `ast-grep`, `comby`, or `libcst`), or grep for the bare string segment (`"data\."`) and inspect each hit.

- **Indented inline imports** like `    from data.foo import bar  # noqa: PLC0415` are common (lazy imports for cycle-breaking). Anchor-only regex (`^from`) misses them. Use `\s+from` or unanchored.

- **`git mv` into a tree where `__pycache__` survives nests files.** When restructuring (`git mv old/ new/`), if `new/` already exists because `__pycache__` survived a prior `rm`, `git mv` nests files into `new/old/file`. Clean `find . -name __pycache__ -exec rm -rf {} +` before structural moves.

- **`_dispatch.py` and union resolvers must be updated when types are renamed/moved.** This trap surfaces only at runtime in test failures ("No module named 'models'"), not at import time. After any rename, grep for the old string in `_dispatch.py`, union resolvers, and lazy refs.

- **Output deprecated fields must be exhaustively grepped from the legacy tree.** Run `git grep -n deprecation_reason <legacy-tree-sha>` and check every hit is carried forward. Toshi-api missed 2 output fields + 1 input field on `OpenquakeHazardSolution` / `OpenquakeHazardTask`; only caught in prod from a real client query (hotfix #344).

- **The Graphene `ClientIDMutation` payload shape must be preserved exactly.** Existing clients use the camelCase `clientMutationId` echo and the `<entityName>` field in the payload. Don't "improve" the shape during migration.

---

## Phase 3 — Test infrastructure

### Goals
Set up a parallel test stack that can validate the new code against real DynamoDB / ES behaviour, while letting all existing tests keep running.

### Steps

1. **Convert `tests/conftest.py` to `testcontainers`:**
   ```python
   # tests/conftest.py
   import os
   os.environ.setdefault("TESTING", "1")  # ← must be set at MODULE LOAD, before app imports

   from testcontainers.core.container import DockerContainer
   # spin only the backing services this API actually uses:
   #   - DynamoDB Local (if any DynamoDB write paths)
   #   - Elasticsearch 7.1.0 (toshi-api only — others don't use ES)
   # see toshi-api graphql_api/tests/conftest.py for the full version
   ```
   Tailor to the target API. Models/Kororaa have read-only data paths — testcontainers may not be needed at all (boto3 mocks via `moto` are lighter). Hazard/Solvis have write paths — DynamoDB Local is justified.

2. **Auth bypass for the rest of the suite.** With `TESTING=1` set at module load, `AuthExtension` short-circuits to a synthetic `local-dev` user with both `read` and `write` scopes. Existing tests run unchanged.

3. **The no-bypass rule of thumb** (lift this verbatim into the new repo's `CLAUDE.md`):
   > Any resolver or code path that reads `info.context["current_user"]` (scopes, userId, authMethod) to make a decision must have at least one test that **disables** the `TESTING=1` bypass and exercises real enforcement. See the `no_bypass` fixture and `_FakeRequest` pattern in `graphql_api/tests/test_auth.py`. Without it, the test silently passes under the synthetic user (which holds both scopes) and the real denial path is never exercised.

   This rule only matters once auth lands. Capture it in `CLAUDE.md` regardless so future-you doesn't forget.

4. **Strawberry test schema:** when constructing a one-off schema in a test, set `config=StrawberryConfig(auto_camel_case=False)` to match production. Otherwise `do_write` becomes `doWrite` in test output and assertions fail mysteriously.

5. **HTTP integration tests via Starlette `TestClient`.** Validates the FastAPI wiring end-to-end (request → Mangum context → AuthExtension → schema → response). At minimum: 1 happy-path query, 1 mutation, 1 anonymous-rejection (once auth lands).

6. **SDL parity check.** A CI job that diffs `schema.legacy.graphql` (from Phase 0) against the new schema's dump and fails on any non-`@deprecated` removal. See toshi-api `graphql_api/tools/schema_parity.py`.

7. **Client query corpus replay** (the second CI job). Replay every vendored client query against the test stage deploy. Catches runtime regressions that SDL parity misses.

### 🚧 Traps

- **`testcontainers` needs Docker daemon running** locally and in CI. Add a doc note + CI service container.
- **`testcontainers[dynamodb]` extra does not exist.** Use bare `testcontainers>=4.0`; `uv lock` warns if you spell the extra.
- **Java is required for DynamoDB Local.** Surfaced as a non-obvious testcontainers error. Document in `DEVELOPMENT.md`.
- **`TESTING=1` set inside a fixture is too late.** It must be at module-load time in `conftest.py` (use `os.environ.setdefault` so the dev's local env wins if explicitly set).

---

## Phase 4 — Deploy, CI & deps hardening

This is the densest section. Every item here corresponds to a real incident or near-miss during the toshi-api migration.

### 4.1 Stage cutover

- Adopt a `deploy-test` branch + `deploy-test → main` promote-PR pattern. Stages: `test` deployed from `deploy-test`, `prod` deployed from `main`.
- Drop default `DB_READ_ONLY` env var. Write-by-default; opt-in to read-only via `serverlessIfElse` per stage. Toshi-api had it as a default with a per-stage drop; the per-stage drop was forgotten in a refactor and prod went read-only (hotfix #343).

### 4.2 GitHub Environments

- Secrets live in **GitHub Environments** (`AWS_TEST`, `AWS_PROD`), not at repo level. The shared deploy workflow takes an `environment:` parameter and uses `secrets: inherit` from the calling workflow.
- **`gh secret list` at repo level does NOT show environment secrets** — this is a 30-min "where is `NZSHM22_TOSHI_API_KEY` coming from" detour. Use `gh secret list --env <NAME>`.

### 4.3 Legacy API key resolution chain

Preserve unchanged for existing clients:

```yaml
# serverless.yml
provider:
  environment:
    LEGACY_API_KEY: ${env:NZSHM22_TOSHI_API_KEY, env:LEGACY_API_KEY, ''}
```

The Lambda Authorizer's Priority-1 check compares incoming `x-api-key` against this env. See toshi-api `auth/authorizer/handler.py:162` (`validate_legacy_api_key`).

### 4.4 Lambda memory sizing

- **Don't drop hard.** Toshi-api went 8GB legacy → 1GB POC (too aggressive, caused timeouts) → 4GB corrected.
- Halve from the legacy value; deploy; watch CloudWatch `Lambda Duration` and `Lambda Memory Utilization` over a representative period (24h minimum). Adjust from there.

### 4.5 GitHub Actions branches filter (silent CI skip)

Workflows with:

```yaml
on:
  pull_request:
    branches: [main, deploy-test]
```

only run on PRs whose **base** is `main` or `deploy-test`. Stacked PRs that target a feature branch get **no CI** silently. Remove the `branches:` filter (see toshi-api PR #337) so every PR runs tests regardless of base.

### 4.6 Yarn 4 (Berry) hygiene

- Pin the package manager: `"packageManager": "yarn@4.16.0"` in `package.json`
- `corepack enable` once on each dev/CI machine before any `yarn install`
- Add `.yarnrc.yml`:
  ```yaml
  nodeLinker: node-modules
  npmMinimalAgeGate: "7d"
  npmPreapprovedPackages:
    - "nshm-*"
    - "nzshm-*"
    - "solvis-*"
    - "weka-*"
    - "toshi-*"
  ```
  The age gate refuses npm packages younger than 7 days (supply-chain hardening); the allowlist bypasses it for project-internal packages so dev velocity doesn't suffer.
- `.gitignore` `.yarn/install-state.gz` — it's a 300KB runtime artifact that often gets accidentally committed.
- **After removing a dep from `package.json`, run `yarn install --mode update-lockfile`** to clear it from `yarn.lock`. CI's `yarn install --immutable` catches the drift.

### 4.7 Yarn `resolutions` traps — read this before any deps PR

**Never globally override a transitive dep without checking every consumer's version range.** This bit toshi-api twice in PR #350:

- A global pin of `fast-xml-parser: 5.8.0` (driven by AWS SDK wanting v5) broke `s3rver` (`serverless-s3-local`'s engine), which still uses the v3 API:
  ```
  ✖ TypeError: xmlParser.parse is not a function
      at new S3ConfigBase (node_modules/s3rver/lib/models/config.js:41:32)
  ```
- Same trap with `@koa/router 9 → 15` — path syntax changed.

The serverless framework loads ALL plugins (including local-dev-only ones like `serverless-s3-local`) at boot time. **A broken local-dev plugin kills prod deploy.**

**Use scoped resolutions** for the divergent consumer:

```jsonc
{
  "resolutions": {
    // AWS SDK keeps its pinned v5 (nested install)
    "s3rver/fast-xml-parser": "3.21.1"
    // No global "fast-xml-parser" override
  }
}
```

**Validate every deps PR locally before pushing:**

```bash
# Verify the broken-here-before packages load
node -e "require('s3rver')"

# Verify serverless plugin chain initialises
STAGE=dummy yarn sls package --stage dummy
# (will fail later on AWS creds — that's fine; the plugin-init step is what we're testing)
```

### 4.8 `uv` hygiene

- `uv lock` after any `pyproject.toml` change. `uv sync` for installs.
- For `pip-audit`: `uv export --format requirements-txt --no-emit-project --output-file audit.txt && uv run pip-audit -r audit.txt -s pypi --require-hashes`
- CI: `uv sync --frozen` to assert the lockfile matches.

### 4.9 Atomic auth source selection (only when JWT auth lands)

> **Sidebar — skip unless you're adding Lambda Authorizer + JWT.** The four siblings currently use `x-api-key` only; this trap is dormant for them. Captured here so future-you finds it when wiring auth.

If a Lambda Authorizer dict is present **at all** in the request scope (`request.scope["aws.event"]["requestContext"]["authorizer"]`), headers must be **ignored entirely**. Do not per-field fallback (authorizer→header) — a partial authorizer mixed with spoofed `X-Auth-Scopes` headers gives an attacker elevated scopes. See toshi-api `graphql_api/auth.py:_extract_auth_context` and `test_partial_authorizer_does_not_fall_through_to_headers`.

### 4.10 Stacked PRs

- Each stacked PR's base = previous step's branch. After the base merges, GitHub auto-rebases the next.
- **For manual rebases use explicit `--onto`:**
  ```bash
  git rebase --onto <new-base> <old-base> <branch>
  ```
  Chained simple rebases (`git rebase <prev>` repeated) confuse git about which commits to replay and can resurrect old commits.

### 4.11 Hotfix forward-port

- A hotfix direct to `main` MUST be cherry-picked back to `deploy-test` (and vice versa) on the same day.
- **Audit branch tips after every promote.** Silent rollbacks happen (GitHub showed PR #346 as merged but the commit was force-pushed away from `deploy-test`; a deps-upgrade PR based on the post-#346 state had to be rebased twice).

### 4.12 Auto-merge polling

If auto-merge is disabled at the repo level (common), poll until CI completes and merge by hand:

```bash
RUN_ID=$(gh pr checks <pr-number> --json link --jq '.[0].link' | grep -oE '[0-9]+$')
until [ "$(gh run view "$RUN_ID" --json status --jq .status)" = "completed" ]; do sleep 30; done
CONCLUSION=$(gh run view "$RUN_ID" --json conclusion --jq .conclusion)
if [ "$CONCLUSION" = "success" ]; then
  gh pr merge <pr-number> --squash --delete-branch
else
  echo "CI conclusion=$CONCLUSION — not merging"
fi
```

### 🚧 Traps (consolidated)

- **A local-dev-only plugin breaks prod deploy.** s3rver, sls-dynamodb, sls-s3-local — they all load at sls boot. Test plugin chain locally before every deps-only PR (`yarn sls package --stage dummy`).
- **`DB_READ_ONLY` defaults are fragile.** Prefer write-by-default with opt-in read-only.
- **`gh secret list` (repo-level) hides environment secrets** — use `--env`.
- **`pull_request.branches:` filter silently skips CI on stacked PRs.** Remove it.
- **Auto-merge polling is mandatory** if the repo doesn't have auto-merge enabled. Don't manually refresh.

---

## Phase 5 — Cutover & validation

### Goals
Ship the new code to the test stage, validate end-to-end, promote to prod, monitor.

### Steps

1. **Establish a healthy baseline before deploying.** Capture the legacy Lambda's current p50/p95/p99 duration, error rate, and invocation count from CloudWatch — this is what "healthy" looks like for comparison post-deploy. Screenshot the dashboard so you don't have to refresh under stress.
2. **Deploy to test stage.** GH Actions on push to `deploy-test`. Watch the deploy run; capture the deployed URL and the API key.
3. **Run the client query corpus** against the test stage. Every query must return the same shape as legacy (modulo `@deprecated` notices on now-deprecated fields).
4. **Spot-check a tiny mutation.** Toshi-api uses a small vendored `runzi` smoke mutation that writes a dummy file (cheap, easy to rollback). Include one in the repo as `tests/smoke/test_mutation_smoke.py`.
5. **Soak the test stage for 24h** before promoting. Re-run the corpus at end of soak; eyeball CloudWatch for the soak window. Skip only if the API has very low real traffic (Model is the obvious candidate to skip).
6. **Pre-stage the rollback PR.** Open it as a draft against `main` with title `revert: <promote-pr-title>` and body containing `git revert <merge-sha>` plus a one-line trigger criterion ("publish if 5xx rate > X% sustained > Y min"). Faster to publish than to author under stress.
7. **Promote `deploy-test → main`** via PR — only after corpus + smoke + soak pass. Use the standard PR title format `release: promote <thing> to prod`.
8. **Watch prod for at least 30 min post-deploy.** Two windows side-by-side:
   - `aws logs tail /aws/lambda/<fn-name> --follow --since 1m` — any unhandled exception, any `5xx`
   - CloudWatch metric graph: invocation count, error rate, p95 duration vs the baseline from step 1
9. **If you roll back:** publish the draft from step 6, merge it, watch the rollback deploy land, then re-run the smoke mutation against prod to confirm legacy behaviour is restored. File a follow-up issue with the failure signature *before* anyone goes to sleep.

### 🚧 Traps

- **A green test stage is not a green prod.** Schema parity passes; corpus passes; smoke passes — and prod still surfaces a single legacy client query that uses a long-deprecated field. The corpus must include real prod traffic samples, not just the queries you remember.
- **Rollback isn't free for stateful changes.** If the new code wrote any DynamoDB items in a new shape during the test window, the legacy code may not read them. Test the rollback path on test stage before going to prod (revert the deploy-test branch, verify it boots, then re-deploy forward).

---

## Per-API addenda

### A1. `nshm-model-graphql-api` — pilot

- **Why first:** smallest (~7 .py files), zip Lambda, no DynamoDB writes, no auth, minimal external integrations. Lowest blast radius.
- **Stack deltas from core:** none. This is the cleanest fit.
- **Migration order within the API:** straightforward — bootstrap → schema (2-3 types only) → tests → deploy.
- **Special handling:** the `nzshm-model` Python library is the heavy lift; it stays untouched.
- **Use this migration to harden the runbook.** Anywhere this doc made you guess: file an issue against `nshm-toshi-api` referencing the runbook line that needed clarification.

### A2. `kororaa-graphql-api`

- **Stack deltas:** read-only boto3 access to external prod `THS_*` DynamoDB tables.
- **Test infra:** no local DynamoDB needed for the production data path; fixtures only need read mocks. `testcontainers` still useful for any internal tables (verify whether any exist).
- **Special handling:** the `TempApiKey` plumbing in `serverless.yml` is the auth posture — preserve unchanged.

### A3. `nshm-hazard-graphql-api`

- **Stack deltas:** container Lambda (Dockerfile + ECR).
- **Container build:** Mangum + FastAPI works the same inside a container. The build pipeline changes; the runtime entry doesn't.
- **The existing `handler.py` workaround goes away.** It exists today because `serverless-wsgi` doesn't cleanly support container Lambda — switching to Mangum (which is packaging-agnostic) makes the workaround unnecessary. Mangum itself isn't doing anything ECR-specific; it just isn't `serverless-wsgi`.
- **Heavy deps:** `matplotlib`, `geopandas`. Watch container image size:
  - Use `python:3.12-slim` base
  - Multi-stage build to drop build deps
  - Aim for <500MB final image (current is likely larger)
- **Memory:** already 4096 MB — keep. Don't try to drop.

### A4. `solvis-graphql-api` — last

- **Stack deltas:** container Lambda + **PynamoDB ORM** + `serverless-dynamodb` local plugin.
- **The big extra:** PynamoDB → boto3 + Pydantic v2 conversion. PynamoDB's declarative Model class becomes a `pydantic.BaseModel` in `<pkg>/data/models.py` plus thin boto3 CRUD helpers in `<pkg>/data/dynamo.py`. See toshi-api `graphql_api/data/models.py` and `graphql_api/data/dynamo.py` for the destination pattern.
- **Yarn `resolutions` hygiene matters here especially** — `serverless-dynamodb` plugin has the same shape of trap as `serverless-s3-local` did for toshi-api. Validate plugin chain locally on every deps PR.
- **`cli` and `cli_ab_test` scripts** import from the package — when the package layout changes (e.g. adopting `_base/_interfaces/_infra`), those imports break. Add them to the test matrix.
- **Migration order within the API:** bootstrap → data layer (PynamoDB→Pydantic) → schema → tests → deploy. The data-layer step is bigger than for the other three APIs.

---

## Appendix

### A. Reference commits / PRs in `nshm-toshi-api`

| Topic | Reference |
|---|---|
| Vendored runzi query corpus | commit `f2f7b43`, file `graphql_api/tools/refresh_runzi_corpus.py` |
| Deprecated field hotfix | commit `edb0c97`, PR #344 |
| Auth parity (AuthExtension) | PR #328, issue #327 |
| ADR-004 code reorganization | PR #329 (omnibus) / split stack #331-#336 |
| `/graphql` URL preserved | PR #340 |
| Lambda memory bump 1→4 GB | PR #342 |
| `DB_READ_ONLY` default removal hotfix | PR #343, PR #346 |
| Deps upgrades | PR #348 (deploy-test), PR #349 (prod) |
| `fast-xml-parser` / `s3rver` hotfix | PR #350 |
| GitHub Actions branches filter removal | PR #337 |
| Ruff lint cleanup after consolidation | PR #338 |

### B. Critical files in `nshm-toshi-api` to copy/adapt

| File | What it shows |
|---|---|
| `graphql_api/app.py` | FastAPI + Mangum entry |
| `graphql_api/schema.py` | Strawberry schema wiring, `AuthExtension`, `auto_camel_case=False` |
| `graphql_api/auth.py` | `AuthExtension` + atomic source selection |
| `graphql_api/models/_infra/_dispatch.py` | clazz_name → module-string dispatch (runtime-string trap) |
| `graphql_api/models/_base/`, `_interfaces/`, `_infra/` | Layered model structure |
| `graphql_api/models/openquake_hazard_solution.py:82-97` | Deprecated **output** field pattern |
| `graphql_api/models/openquake_hazard_task.py:162-165` | Deprecated **input** field pattern (`strawberry.field`, not `strawberry.argument`) |
| `graphql_api/data/models.py` | Pydantic v2 data layer |
| `graphql_api/tests/conftest.py` | testcontainers + `TESTING=1` bypass |
| `graphql_api/tests/test_auth.py` | `no_bypass` fixture, `_FakeRequest`, anti-spoofing test |
| `graphql_api/tools/schema_parity.py` | SDL parity CI check |
| `graphql_api/tools/refresh_runzi_corpus.py` | Client query corpus pattern |
| `serverless.yml` | Mangum handler, stage-specific config via `serverlessIfElse`, LEGACY_API_KEY resolution |
| `pyproject.toml` | Ruff `select`/per-file-ignores, mypy overrides for `models/*` |
| `.yarnrc.yml` | `npmMinimalAgeGate`, preapproved packages |
| `package.json` `resolutions` | Both the working pattern AND the cautionary tale |
| `CLAUDE.md` "Auth in tests" section | Verbatim rule of thumb |

### C. Traps index (one-line each, for fast scanning)

| # | Phase | Symptom | Fix |
|---|---|---|---|
| 1 | 0 | New SDL passes parity check, prod query still breaks | Vendor real client queries; replay against test stage |
| 2 | 1 | Existing clients break post-migration on field names | `StrawberryConfig(auto_camel_case=False)` |
| 3 | 1 | CI suddenly fails 89 ruff errors after stack consolidation | Add per-file-ignores up front |
| 4 | 2 | `from data.foo import bar` left behind after rename | Use AST refactor, not anchored regex |
| 5 | 2 | `git mv` creates `new/old/file.py` nesting | `find . -name __pycache__ -delete` first |
| 6 | 2 | "No module named 'models'" at runtime in tests | Update `_infra/_dispatch.py` + lazy-ref strings |
| 7 | 2 | Prod `Cannot query field X on type Y` | Grep legacy tree for `deprecation_reason`; carry all forward |
| 8 | 2 | `@deprecated` missing on input field | Use `strawberry.field`, not `strawberry.argument` |
| 9 | 3 | Tests pass under `TESTING=1` but real auth path is broken | Add no-bypass tests for any `current_user`-reading code |
| 10 | 3 | `testcontainers[dynamodb]` not found | Use bare `testcontainers>=4.0`; Java required for DDB Local |
| 11 | 4 | Existing clients suddenly hit auth | Preserve `LEGACY_API_KEY` chain in `serverless.yml` |
| 12 | 4 | Prod write returns `DB_READ_ONLY` | Drop the default; opt-in to RO via `serverlessIfElse` |
| 13 | 4 | Can't find where `NZSHM22_*` secret is set | `gh secret list --env AWS_TEST/AWS_PROD` |
| 14 | 4 | Stacked PR doesn't run CI | Remove `branches:` filter on workflow |
| 15 | 4 | `yarn install --immutable` fails after removing a dep | `yarn install --mode update-lockfile` first |
| 16 | 4 | Deploy dies at plugin init: `xmlParser.parse is not a function` | Scope resolutions to the affected consumer; drop global override |
| 17 | 4 | Prod deploy crashes after a deps-only PR | Run `yarn sls package --stage dummy` locally before push |
| 18 | 4 | Stacked-PR rebase resurrects old commits | Use `git rebase --onto <new-base> <old-base> <branch>` |
| 19 | 4 | Hotfix landed on main, deploy-test silently rolled back | Audit branch tips after every promote |
| 20 | 4 | Lambda timeouts after memory drop | Halve from legacy and monitor CloudWatch; don't cut hard |
| 21 | 5 | Rolling back fails because new code wrote new-shape DDB items | Test the rollback path on test stage before going to prod |
| 22 | 5 | "Healthy" prod after deploy is hard to judge | Screenshot pre-deploy CloudWatch baseline (step 1) |

---

## Ownership & on-call posture

- **Per-migration owner.** Each sibling migration nominates one engineer as owner before kickoff. They drive the work, sign off the promote PR, and stay reachable for 24h after prod deploy.
- **Reviewer.** Promote PR (`deploy-test → main`) requires review from someone who didn't write the migration.
- **Prod AWS access.** At least two engineers must have working AWS-prod admin during the cutover window. Confirm `aws sts get-caller-identity` against the prod profile the day before.
- **Comms.** Cutover updates posted to the team Slack channel (or equivalent) at: deploy start, test-stage soak start, promote PR open, prod deploy start, "healthy" call (30 min post-deploy), or rollback decision.
- **API Gateway URL.** Preserve the existing path (`/graphql`) — clients are hardcoded. If you stage on a new path (`/graphql-v2`), plan the cutover to flip back before clients are pointed at it (see toshi-api PR #340 — this trap caught us).

## Maintenance

- This runbook is owned by whoever last shipped a migration using it.
- Every sibling migration MUST file at least one PR against this doc: either confirming "no changes needed" in a one-line note, or adding clarifications / new trap entries.
- After all four siblings migrate, do a retrospective pass — collapse anything that turned out to be toshi-api-specific, promote anything from per-API addenda that turned out to be general.
