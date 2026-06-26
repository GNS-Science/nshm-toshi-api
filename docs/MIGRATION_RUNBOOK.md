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
- **Importing the legacy schema can pollute the SDL dump via stdout.** The `print(str(schema))` snippet above captures *everything* on stdout — including dependency warnings emitted at import time (Model pilot: `nzshm-model` prints `WARNING: optional 'toshi' dependencies are not installed`). Those lines land in `schema.legacy.graphql` and break the parity baseline. Redirect stdout→stderr around the schema import (`contextlib.redirect_stdout(sys.stderr)`), then print the SDL.

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
- **`<pkg>/schema.py` may already be taken by the legacy schema.** If the Graphene code lives in a `schema/` *package* (not a `schema.py` module), that import path is occupied — Step 4 can't create `schema.py` yet. Use a transitional name (Model pilot used `strawberry_schema.py`) during the migration and rename to `schema.py` at cutover, once the legacy `schema/` package is deleted. Update `app.py` + test imports in the same rename commit.
- **Dropping `serverless-wsgi` does NOT drop Python-dep packaging.** A common worry after Step 5 is "what now zips the deps into the Lambda?" On Serverless Framework v4 the answer is the **built-in** python-requirements step (see §4.8), activated by a `custom.pythonRequirements` block and uv-aware. Removing `serverless-wsgi` leaves it running. Don't add `serverless-python-requirements` back as a plugin.

- **The `poetry2uv` skill flips mypy strict via `follow_untyped_imports = true`.** It writes a `[tool.mypy]` block with `follow_untyped_imports = true`, which makes CI mypy type-check *into* the legacy Graphene + untyped lib code (e.g. `solvis`, `geopandas`) — surfacing dozens of errors in modules you haven't touched and were green before. Restore the original lenient posture (`ignore_missing_imports = true` only) and keep the per-file `exclude`; the legacy modules are deleted at cutover anyway. (Solvis: 29 spurious errors, all in to-be-deleted graphene modules; CI red on every PR until reverted.)

- **Container Lambda + `serverless-plugin-warmup`: Mangum needs a warmup-event guard.** The warmup plugin pings the function every few minutes with a **non-HTTP** event (`{"source": "serverless-plugin-warmup"}`). Mangum can't infer a handler for it → `RuntimeError` on every ping (the old `serverless-wsgi` handler silently swallowed these). Guard it in the entry **before** delegating to Mangum:
  ```python
  _mangum = Mangum(app)
  def handler(event, context):
      if isinstance(event, dict) and event.get("source") == "serverless-plugin-warmup":
          return {"statusCode": 200, "body": "warmed"}
      return _mangum(event, context)
  ```
  **Nothing but live warmup traffic surfaces this** — in-process tests, the HTTP `TestClient`, and the deploy smoke all pass; you only see it tailing prod logs (or a unit test that feeds the handler a warmup event). Applies to every container sibling using the plugin (Hazard next).

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

- **Relay `Node` — watch the `id` scalar for SDL parity.** The per-type pattern above uses `relay.Node` / `relay.NodeID[str]` (what toshi-api ships). But Strawberry's relay emits a `GlobalID` scalar and `id: GlobalID!`, whereas a legacy **graphene-relay** schema exposes `id: ID!`. If your parity baseline (Phase 0) has `id: ID!`, `relay.Node` will fail the parity gate and may change the wire id. Two options: (a) accept the `GlobalID` SDL change if no client pins `id`'s type, or (b) for strict parity, hand-write a custom `@strawberry.interface Node` with `id: strawberry.ID` and encode/decode via `graphql_relay.to_global_id` / `from_global_id` (Model pilot's choice — reproduces graphene byte-for-byte). Composite ids built from several fields also don't fit `relay.NodeID[str]` cleanly; the custom interface handles those.
- **Cycle-breaking:** `Annotated["Bar", strawberry.lazy("path.to.bar")]` for forward refs between types.
- **Runtime dispatch (conditional):** only needed if your API has polymorphic node lookup by a stored `clazz_name` (typical when one DynamoDB table holds multiple GraphQL types). Build a dispatch table (see toshi-api `graphql_api/models/_infra/_dispatch.py`). **Every new domain type must be registered here** or `node()` returns `None` for it. Models / Kororaa likely don't need this; Solvis / Hazard might.
- **Layered models** (recommended for any package with >10 types):
  - `<pkg>/models/_base/` — storage-aligned shared types (e.g. `thing`, `file`, `table`)
  - `<pkg>/models/_interfaces/` — GraphQL interfaces shared by domain types
  - `<pkg>/models/_infra/` — scalars, common enums, dispatch table, unions
  - `<pkg>/models/<domain>.py` — flat domain types
  - See toshi-api `graphql_api/models/` for the reference.
- **Pydantic v2 in the data layer:** keep DynamoDB shapes in `<pkg>/data/models.py` as `pydantic.BaseModel` classes (e.g. `FooData`), separate from the Strawberry `Foo`. `from_dict` does the validation + projection. This separation makes data migrations isolated from schema migrations. **Caveat:** this assumes you *own* the data layer. When an upstream library already exposes typed models (Model pilot reads `nzshm-model`'s stdlib dataclasses), reuse those as the data layer and write resolvers against them directly — don't mirror them into a parallel pydantic shape. Your Strawberry types stay a thin projection either way.
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

- **Strawberry makes output fields non-null by default — graphene didn't.** A resolver typed `-> str` emits `String!`; the equivalent graphene `String` field was nullable (`String`). Annotate `-> str | None` (or `Optional[str]`) to match the legacy SDL. This applies to *every* scalar field — tightening the contract mid-migration is a parity break the SDL gate will catch, but only if your Phase 0 baseline is accurate.

- **Optional args render a `= null` default that graphene omits.** `def field(self, version: str | None = None)` produces `version: String = null` in the SDL; legacy graphene emits `version: String`. Use `strawberry.UNSET` as the default (`version: str | None = strawberry.UNSET`) to suppress the `= null` and match.

- **An input *instance* as an arg/field default renders in the SDL but breaks runtime coercion.** Reproducing a graphene `default_value=dict(...)` with a Strawberry input *instance* (`style: Foo = Foo(...)`) prints the right default in the SDL **but** graphql-core then tries to coerce that already-built instance at execution and raises *"Expected type 'Foo' to be a mapping"*. Use a plain **mapping** as the default instead (`style: Foo = {"stroke_color": "black", ...}`) — it both renders and coerces. (Solvis hit this twice: a geojson style arg and a nested `filter_set_options` default.)

- **Graphene fills *partial* input defaults from the input type's own field defaults — match the value *types*.** A graphene `default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0)` (3 keys) is coerced through the input type, so the omitted `fill_opacity`/`fill_color` come back filled from the **field** defaults. Reproduce those field defaults with the right type (`fill_opacity: float | None = 1.0`, not `= 1`) or the JSON output differs by `1.0` vs `1` and the byte-compare fails. The SDL gate won't catch it — only a runtime differential will (see Phase 3).

- **Custom scalars and enums-from-untyped-libs trip mypy `valid-type`.** A `strawberry.scalar(NewType(...))` or `strawberry.enum(some_untyped_lib.Enum)` assigned to a module variable isn't seen as a usable type in annotations. Wrap it in a `TYPE_CHECKING` alias to a concrete stub:
  ```python
  if TYPE_CHECKING:
      JSONString = object               # opaque to mypy
      class SetOperationEnum(enum.Enum): UNION = "UNION"; ...   # concrete stub
  else:
      JSONString = strawberry.scalar(...)
      SetOperationEnum = strawberry.enum(lib.SetOperationEnum, ...)
  ```
  (Model used a single `# type: ignore[valid-type]` for one scalar; Solvis needed this for `JSONString` + a `SetOperationEnum` from `solvis`.)

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

### The differential harness is the highest-value Phase 3 artifact

SDL parity proves the *shape*; it is blind to **runtime** divergence. Build a tiny in-process
differential — run each query through **both** schemas (legacy Graphene + new Strawberry, same
process, same fixtures) and assert identical `data`:

```python
def _assert_parity(query, **vars):
    legacy = Client(schema_root).execute(query, variable_values=vars or None)
    straw  = strawberry_schema.execute_sync(query, variable_values=vars or None)
    assert straw.data == legacy["data"]
```

It is cheap and it catches the things the SDL gate **cannot** — Solvis found three real bugs
this way that were byte-identical in the SDL: the relay **global-id** encoding (`id` must be
`graphql_relay.to_global_id(...)`, not raw — the C1 trap, live), **float-vs-int** default values,
and the input-instance-vs-mapping coercion. Seed it from the vendored corpus; for archive/data
fixtures, reuse the existing test fixtures. It's also the in-process rehearsal for the live A/B
(`cli_ab_test` / `drive_live.py`) at cutover.

---

## Phase 4 — Deploy, CI & deps hardening

This is the densest section. Every item here corresponds to a real incident or near-miss during the toshi-api migration.

### 4.1 Stage cutover

- Adopt a `deploy-test` branch + `deploy-test → main` promote-PR pattern. Stages: `test` deployed from `deploy-test`, `prod` deployed from `main`.
- Drop default `DB_READ_ONLY` env var. Write-by-default; opt-in to read-only via `serverlessIfElse` per stage. Toshi-api had it as a default with a per-stage drop; the per-stage drop was forgotten in a refactor and prod went read-only (hotfix #343).

### 4.2 GitHub Environments

- Secrets live in **GitHub Environments** (`AWS_TEST`, `AWS_PROD`), not at repo level. The shared deploy workflow takes an `environment:` parameter and uses `secrets: inherit` from the calling workflow.
- **`gh secret list` at repo level does NOT show environment secrets** — this is a 30-min "where is `NZSHM22_TOSHI_API_KEY` coming from" detour. Use `gh secret list --env <NAME>`.
- **This `AWS_TEST`/`AWS_PROD` + OIDC split is the toshi-api posture, not a universal one.** Confirm the target sibling's actual setup before assuming it. The Model pilot deploys from **repo-level static AWS keys** (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`) plus a single `DEPLOY_TEST` environment that holds *no* environment secrets — no per-env split, no OIDC role to preserve. Inventory first (Phase 0); migrating a sibling *toward* the toshi-api posture is a separate hardening task, out of scope for the code migration.

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

only run on PRs whose **base** is `main` or `deploy-test`. Stacked PRs that target a feature branch get **no CI** silently — annoying mid-migration.

> ⚠️ **This filter is often a deliberate supply-chain control — do NOT remove it reflexively.** It narrows the set of PRs that auto-trigger the build. The risk it mitigates (raised by voj on solvis): an **anonymous / outside PR auto-running CI** is a supply-chain vector — the build `uv sync`s untrusted deps and runs the PR's checked-out code in the runner. (`pull_request` withholds secrets from fork PRs and runs the *base* branch's workflow, so secrets aren't directly exposed — but arbitrary code execution + dep install on a well-crafted PR is the attack surface.) Pair the filter with GitHub's **"require approval to run workflows on fork PRs"** setting; never switch to `pull_request_target` to "fix" CI coverage.

**So:** if a stacked migration needs CI on feature-branch PRs, get it **without** weakening the control —
- merge the stack as **one combined PR** (G7) and rely on that PR's CI (what solvis ended up doing), or
- run CI on a stacked branch on demand with `workflow_dispatch`, or
- widen temporarily, then **restore the filter** before promote.

Solvis lived this: removed the filter in Phase 1 for stacked-PR CI, voj flagged it as the deliberate anti-supply-chain rule, restored before the prod promote. (toshi-api PR #337 removed it there in a different threat context — confirm your repo's fork-PR posture before copying.)

- **If you do widen it for a stack, the change must reach every head branch.** For same-repo PRs, GitHub runs the workflow file as it exists on the PR's **head** branch — removing the filter on the bottom branch doesn't retroactively give CI to the PRs stacked above it. (One more reason to prefer the combined-merge route over widening.)

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

> **SF v4 + Python: `sls package` won't produce a local zip.** On a Serverless Framework v4 Python project, `yarn sls package` always resolves the AWS account id first (even offline, even with no `org`/`app`), so it stops before building the zip without credentials. You can still validate plugin/config init this way, but the *definitive* packaging proof is the first test-stage deploy (Model pilot: local packaging was blocked; the test-stage deploy is what confirmed the built-in requirements step works — see §4.8).

### 4.8 `uv` hygiene

- `uv lock` after any `pyproject.toml` change. `uv sync` for installs.
- For `pip-audit`: `uv export --format requirements-txt --no-emit-project --output-file audit.txt && uv run pip-audit -r audit.txt -s pypi --require-hashes`
- CI: `uv sync --frozen` to assert the lockfile matches.
- **`bump2version` / `bumpversion` does not touch `uv.lock`.** It bumps `pyproject.toml`, `package.json`, `__init__.py` — but `uv.lock` records the project's own version too, so after a bump `uv lock --check` fails. Pair every version bump with a follow-up `uv lock` commit (Model pilot: caught by CI's lock check).
- **How Python deps get packaged after `serverless-wsgi` is gone (SF v4).** Serverless Framework v4 ships **python-requirements built-in** — no plugin needed. It activates on the presence of a `custom.pythonRequirements` block (SF prints this at deploy time) and is **uv-aware**. Pattern Model used: keep `custom.pythonRequirements` (with e.g. `dockerizePip`, `slim`, `noDeploy: [botocore]`); have the `deploy` script run `uv export` → `requirements.txt` before `serverless deploy` for a deterministic input; leave `plugins: []`. Removing `serverless-wsgi` does **not** remove this step. The package `patterns` (`!**` + `<pkg>/**`) only scope your *source*, not the deps.

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
- **If an intermediate phase isn't independently deployable, merge the stack as one unit.** Phase boundaries are good for *review*, but a mid-stack branch can be a non-runnable state (Model pilot's P1 is a minimal stub schema that doesn't serve the real types yet). On a repo where merging the bottom branch triggers a deploy (`deploy-test`), landing phases one-by-one would deploy that broken intermediate. Instead, retarget the top PR's base to the deploy branch and do **one combined merge → one deploy** (Model: #67 carried #63–#66; the others closed as "landed via #67").

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
- **`pull_request.branches:` filter silently skips CI on stacked PRs** — but it's often a deliberate **supply-chain control** (stops anonymous/fork PRs auto-running the build). Don't remove it reflexively; get stacked-PR CI via the combined-merge route (G7) or `workflow_dispatch`, and restore it before promote. See §4.5.
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
   - **Low-traffic alternative — active differential validation, not a passive soak.** With little real traffic, a soak and a CloudWatch baseline tell you nothing. Instead, drive the live `/graphql` yourself and diff each response **byte-for-byte against an in-process oracle** (the new schema executed locally, already proven == legacy). Enumerate the full surface — every entity/version, a `node(id)` per Relay type, and the vendored corpus. The rollback trigger becomes "the driver reports any mismatch", not a metric threshold. Model pilot ran this against both the live legacy test **and prod** stages (read-only): 19/19 byte-identical, which retired the parity risk *before* cutover. See `tests/smoke/drive_live.py` in `nshm-model-graphql-api`.
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
- **Pilot migration log:** `nshm-model-graphql-api/docs/MIGRATION_LOG.md` is the worked record — stacked PRs per phase, SF v4 built-in packaging proven on the test-stage deploy, and byte-for-byte differential validation against the live legacy test **and** prod stages. The traps and clarifications it surfaced are folded back into this runbook (Phase 0 SDL-dump stdout, Phase 1 `schema.py` name clash, Phase 2 `GlobalID`/nullability/`UNSET` parity, §4.5/4.7/4.8/4.10 deploy items, the Phase 5 differential-validation alternative).

### A2. `kororaa-graphql-api`

- **Stack deltas:** read-only boto3 access to external prod `THS_*` DynamoDB tables.
- **Test infra:** no local DynamoDB needed for the production data path; fixtures only need read mocks. `testcontainers` still useful for any internal tables (verify whether any exist).
- **Special handling:** the `TempApiKey` plumbing in `serverless.yml` is the auth posture — preserve unchanged.

### A3. `nshm-hazard-graphql-api`

- **Stack deltas:** container Lambda (Dockerfile + ECR).
- **Container build:** Mangum + FastAPI works the same inside a container. The build pipeline changes; the runtime entry doesn't.
- **The existing `handler.py` workaround goes away.** It exists today because `serverless-wsgi` doesn't cleanly support container Lambda — switching to Mangum (which is packaging-agnostic) makes the workaround unnecessary. Mangum itself isn't doing anything ECR-specific; it just isn't `serverless-wsgi`.
- **Heavy deps:** `matplotlib`, `geopandas`. Watch container image size — but **don't reach for multi-stage reflexively**: Solvis (same geo stack: matplotlib + geopandas + pyproj + shapely + solvis) came in at **360 MB single-stage** on the `public.ecr.aws/lambda/python:3.12` base, comfortably under the 500 MB aim. Measure first; only multi-stage if you're actually over.
- **`serverless-plugin-warmup` warmup-event guard** — see the Phase 1 trap. Hazard is a container Lambda with the warmup plugin, so its Mangum entry needs the same guard or prod logs fill with `RuntimeError` every few minutes.
- **Memory:** already 4096 MB — keep. Don't try to drop.

### A4. `solvis-graphql-api` — last

- **Stack deltas:** container Lambda + **PynamoDB ORM** + `serverless-dynamodb` local plugin.
- **The big extra:** PynamoDB → boto3 + Pydantic v2 conversion. PynamoDB's declarative Model class becomes a `pydantic.BaseModel` in `<pkg>/data/models.py` plus thin boto3 CRUD helpers in `<pkg>/data/dynamo.py`. See toshi-api `graphql_api/data/models.py` and `graphql_api/data/dynamo.py` for the destination pattern.
- **Yarn `resolutions` hygiene matters here especially** — `serverless-dynamodb` plugin has the same shape of trap as `serverless-s3-local` did for toshi-api. Validate plugin chain locally on every deps PR.
- **`cli` and `cli_ab_test` scripts** import from the package — when the package layout changes (e.g. adopting `_base/_interfaces/_infra`), those imports break. Add them to the test matrix.
- **Migration order within the API:** bootstrap → data layer (PynamoDB→Pydantic) → schema → tests → deploy.

**What the migration actually found (2026-06, completed **in prod** — promote + 30-min watch clean):**
- **The PynamoDB surface was tiny, not a big data layer.** It was a *single* model (`BinaryLargeObjectModel`, 5 attrs) already wrapped by a hand-written class. Convert the `Model` to a `pydantic.BaseModel` + thin boto3 CRUD **behind the unchanged wrapper API** so `cli`/resolvers don't move — `pynamodb` drops out entirely. The "data-layer step is bigger" caveat above didn't hold.
- **Reproduce `JSONAttribute` as a JSON *string*, not a native DynamoDB Map.** A native Map round-trips numbers as `Decimal`; storing the JSON-dumped string keeps ints as ints and keeps `to_json()` byte-equal.
- **Reuse the in-repo `cli_ab_test` for cutover validation — don't build a `drive_live.py`.** Its checks already cover the full client surface; `cli_ab_test -A prod -B test` gave the 9/9 gate. (Model had to build `drive_live.py` because it had no equivalent.)
- **For the heaviest resolvers, *delegate* to the legacy Graphene resolvers rather than re-port.** Solvis's `CompositeRuptureSections` (aggregates + MFD + geojson + colour) was ported by building a graphene root from the Strawberry input and calling the legacy static resolvers (held as `strawberry.Private`); the compute is reused verbatim, rewired onto the kept helpers at cleanup. Far less risk than rewriting pandas/geopandas logic.
- **`relay.Node` → custom interface for `id: ID!` parity (C1) is mandatory here too** — and the live differential caught the *encoding* (`to_global_id`), which SDL parity can't see.

**Post-cutover legacy cleanup (de-graphene) — what removing Graphene actually taught us:**
- **Remove Graphene in verified chunks, each gated on SDL parity + the test suite — not one big delete.** Extract each Graphene-free compute helper to a stable home (Solvis: `color_scale/compute.py`, `composite_solution/ruptures.py`, `cached.py`, `geojson_style_util.py`), rewire the Strawberry resolver onto it, verify against the still-present Graphene, then delete. The *delegated* resolvers (the `CompositeRuptureSections` `strawberry.Private` trick above) must be **de-delegated** the same way before the Graphene root can go. Net for Solvis: −1740 lines of Graphene across ~12 modules; the whole package then imports zero `graphene`.
- **Deleting Graphene kills the differential test's oracle — and snapshots are NOT a drop-in replacement.** The in-process differential ran the *same query through both schemas in one process*, so platform float differences (shapely/geos coords, matplotlib hexes) cancelled. Capture those as golden snapshots on macOS and ubuntu CI fails the byte-compare on the low float digits. Fix: keep byte-exact snapshots only for **deterministic** queries (rounded scalars, enums); assert geometry/geojson/colour **structurally** (counts, the global-id encoding decodes, "styling reached every feature"). `cli_ab_test` (same live data, both stages) stays the authoritative geojson parity gate. *Also drop accidental megafixtures — a `get_locations` snapshot re-stored the whole `nzshm_common` LOCATIONS constant as a 118k-line file.*
- **Keep and *repoint* the legacy Graphene-`Client` tests at the Strawberry schema — don't delete them.** A `graphene.test.Client` drop-in (`tests/_strawberry_client.py`, ~25 lines) runs all of them unchanged against Strawberry; they cover the resolvers you *reimplemented*, far past the parity corpus. They caught a real bug: `filter_ruptures` passed `strawberry.UNSET` as the sortby `ascending` (pandas rejected it) — invisible to SDL parity.
- **Codecov fails on the *promote* PR's cumulative diff, not your last commit.** The whole `deploy-test → main` diff is measured against `main`; the migration sat ~0.2% under the auto-bar. The culprit was a standalone tool script (the SDL-parity gate) at **0% coverage** — wrap such tools as pytest tests (which also makes the gate permanent). Don't fake-cover genuinely-unreachable legacy branches; use `# pragma: no cover` with a note.
- **A/B with valid inputs can't see malformed-input behaviour — and that's OK.** Prod logged a `KeyError` from a client sending `fault_system: ""`; the failing line was unchanged shared compute Graphene called identically (HTTP 200 + a per-field GraphQL error, not 5xx). Not a regression — don't let it trigger a rollback; file it as a separate robustness item.

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
| 14 | 4 | Stacked PR doesn't run CI | `branches:` filter is often a deliberate supply-chain control — combined-merge (G7), don't just remove it (§4.5) |
| 15 | 4 | `yarn install --immutable` fails after removing a dep | `yarn install --mode update-lockfile` first |
| 16 | 4 | Deploy dies at plugin init: `xmlParser.parse is not a function` | Scope resolutions to the affected consumer; drop global override |
| 17 | 4 | Prod deploy crashes after a deps-only PR | Run `yarn sls package --stage dummy` locally before push |
| 18 | 4 | Stacked-PR rebase resurrects old commits | Use `git rebase --onto <new-base> <old-base> <branch>` |
| 19 | 4 | Hotfix landed on main, deploy-test silently rolled back | Audit branch tips after every promote |
| 20 | 4 | Lambda timeouts after memory drop | Halve from legacy and monitor CloudWatch; don't cut hard |
| 21 | 5 | Rolling back fails because new code wrote new-shape DDB items | Test the rollback path on test stage before going to prod |
| 22 | 5 | "Healthy" prod after deploy is hard to judge | Screenshot pre-deploy CloudWatch baseline (step 1) |
| 23 | 0 | `schema.legacy.graphql` baseline has stray `WARNING:` lines | Redirect stdout→stderr around the schema import in the SDL dump |
| 24 | 1 | Can't create `<pkg>/schema.py` — legacy `schema/` package owns the path | Transitional name (`strawberry_schema.py`); rename at cutover |
| 25 | 2 | Parity gate fails: new `id: GlobalID!` vs legacy `id: ID!` | Custom `@strawberry.interface Node` + `graphql_relay` encode/decode |
| 26 | 2 | New scalar field is `String!`, legacy was nullable `String` | Annotate resolvers `-> str \| None` |
| 27 | 2 | Arg renders `version: T = null`; legacy emits `version: T` | Default the arg to `strawberry.UNSET` |
| 28 | 2 | Mirroring an upstream-owned typed model into a parallel pydantic shape | Reuse the upstream dataclasses as the data layer |
| 29 | 4 | "What packages the Python deps after `serverless-wsgi`?" | SF v4 built-in python-requirements (uv-aware), via `custom.pythonRequirements` |
| 30 | 4 | `sls package` won't build a zip locally on SF v4 python | Resolves AWS account id first; prove packaging via test-stage deploy |
| 31 | 4 | `uv lock --check` fails after a version bump | bumpversion skips `uv.lock`; add a paired `uv lock` commit |
| 32 | 4 | Removing the `branches:` filter still leaves stacked PRs CI-less | Cascade-rebase the fix onto every head branch in the stack |
| 33 | 4 | One-by-one stacked merge deploys a broken intermediate | Combined merge → one deploy when a phase isn't independently deployable |
| 34 | 4 | Assumed `AWS_TEST`/`AWS_PROD` env split that doesn't exist | Inventory secrets first; some siblings use repo-level static keys + one env |
| 35 | 5 | Soak is meaningless on a low-traffic API | Active differential validation: drive live, diff byte-for-byte vs oracle |
| 36 | 1 | CI mypy red on untouched legacy code after `poetry2uv` | It set `follow_untyped_imports=true`; restore `ignore_missing_imports` only |
| 37 | 1 | Container Lambda: `RuntimeError` every few min in prod logs | `serverless-plugin-warmup` sends a non-HTTP event; guard it before Mangum |
| 38 | 2 | Input-instance arg default → "expected a mapping" at runtime | Use a plain mapping default, not an input instance (renders + coerces) |
| 39 | 2 | Geojson/output differs by `1.0` vs `1` on default styles | Match input-field default *types* (graphene fills partial defaults via them) |
| 40 | 2 | mypy `valid-type` on a custom scalar / enum-from-untyped-lib | `TYPE_CHECKING` alias to a concrete stub; real value in the `else` branch |
| 41 | 3 | SDL parity green but `id`/values wrong at runtime | In-process differential (same query, both schemas) — catches encoding/defaults |
| 42 | A4 | PynamoDB port feared big; geojson resolvers feared a re-port | One wrapped model → pydantic behind the wrapper; *delegate* heavy resolvers |
| 43 | cleanup | Differential test's oracle deleted with Graphene; snapshots flake on CI | Byte-snapshot deterministic queries only; assert geometry/geojson structurally |
| 44 | cleanup | Deleting the Graphene-`Client` tests loses coverage of reimplemented resolvers | Repoint them at Strawberry via a `graphene.test.Client` drop-in shim |
| 45 | cleanup | Codecov red on the *promote* PR (cumulative diff under auto-bar) | Wrap standalone tool scripts (SDL gate) as pytest tests; `# pragma` truly-dead branches |
| 46 | 5 | Prod `KeyError` on `fault_system:""` post-cutover | Unchanged shared compute — Graphene identical; not a regression, file separately |

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
