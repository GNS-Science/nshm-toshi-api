# Tools

## `schema_parity.py` — legacy ↔ POC SDL diff

Catches schema-level divergences between the legacy Graphene/Flask API
and the Strawberry/FastAPI POC. Designed to surface the class of bugs
that hit production this session before they ship:

- Types missing on one side (e.g. `ToshiFile` renamed to `File`)
- Fields missing on one side (e.g. `GeneralTask.subtask_result`)
- Field type mismatches (e.g. `file_size: BigInt` vs `Int`)
- Mutations missing on one side (e.g. `update_automation_task`)
- Enum value drift (e.g. `DISAGG` task type)
- Union member drift

### Usage

Step 1 — dump the POC SDL (run from `spike/strawberry_poc/`):

```bash
uv run python tools/dump_poc_sdl.py > /tmp/poc.sdl
```

Step 2 — dump the legacy SDL (run from repo root, in the legacy venv):

```bash
uv run python -c "
from graphql.utilities import print_schema
from graphql_api.schema import root_schema
print(print_schema(root_schema.graphql_schema))
" > /tmp/legacy.sdl
```

Step 3 — diff:

```bash
uv run python tools/schema_parity.py /tmp/legacy.sdl /tmp/poc.sdl
```

For CI usage, add `--fail-on-diff` to exit 1 when any divergence is
found. For machine-readable output use `--format json`.

### Allowlisting intentional divergences

The tool is deliberately allow-list-free in this first version. The
report is meant to be read by humans, who decide which divergences are
intentional (e.g. POC adds `BigInt` scalar, drops some legacy-only
bugfix-test types) and which are accidental regressions.

When the divergence set stabilises, a future iteration can add a YAML
allowlist file (`expected_diffs.yaml`) that the tool subtracts from the
diff before checking `--fail-on-diff`.

### Why SDL rather than introspection JSON

Both Graphene's `print_schema` and Strawberry's `schema.as_str()` emit
the same standard SDL format, so the diff is symmetric and doesn't care
which framework produced the schema. The tool uses `graphql-core`'s
parser (already a transitive dep via `strawberry-graphql`) to turn each
SDL into a structural dict before diffing.
