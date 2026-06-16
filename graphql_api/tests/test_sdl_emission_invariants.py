"""SDL emission invariants — catches Strawberry-default footguns before they ship.

The list-element nullability gotcha (documented in `docs/smoke-test-learnings.md`)
slipped through because no test caught it at the schema-build layer. This file
fills that gap: pure SDL inspection, runs as a unit test, no GraphQL execution
required.

The invariants we lock in here exist because:

1. Strawberry's `list[T]` emits `[T!]` (non-null elements) by default.
2. Legacy Graphene emits `[T]` (nullable elements) by default.
3. The two are NOT wire-equivalent for input variables — GraphQL's
   variable-type subsumption check rejects `$x: [T]!` flowing into a `[T!]!`
   position.

Any time a contributor writes `list[T]` in an `@strawberry.input` class, the
SDL drifts further from legacy. This file fails loudly so we notice.
"""

import re

import pytest

from graphql_api.schema import schema


@pytest.fixture(scope="module")
def sdl() -> str:
    return schema.as_str()


# ── Invariant 1: every `input` type's list field uses nullable elements ───────


def test_no_input_type_uses_non_null_list_elements(sdl):
    """Every list-typed field inside an `input` block matches legacy `[T]`,
    not Strawberry's default `[T!]`.

    Failure here is almost certainly because a new `@strawberry.input` class
    declared `list[T]` rather than `list[T | None]`. Fix the Python type
    annotation in the model file, then re-run.
    """
    # Find every `input <Name> { ... }` block
    for input_block in re.finditer(r"input \w+ \{[^}]+\}", sdl, re.DOTALL):
        body = input_block.group(0)
        type_name = re.match(r"input (\w+)", body).group(1)
        # Find every list-typed field
        for field_match in re.finditer(r"^\s+(\w+):\s*(\[[^\]]+\]!?)", body, re.M):
            field_name, field_type = field_match.group(1), field_match.group(2)
            inner = field_type.strip("[]!")
            if inner.endswith("!"):
                pytest.fail(
                    f"Input {type_name}.{field_name} uses non-null list elements "
                    f"({field_type}). Legacy Graphene emits `[T]` (nullable "
                    f"elements). Fix the Python type to `list[T | None]` so "
                    f"runzi-style variables `${field_name}: [T]!` validate. "
                    f"See docs/smoke-test-learnings.md §1."
                )


# ── Invariant 2: critical mutations remain positional, not input-wrapped ──────


def test_create_file_uses_positional_args(sdl):
    """create_file's positional shape must not regress to `input: CreateFileInput!`.

    nshm-toshi-client sends it as `create_file(file_name:, md5_digest:, …)`.
    """
    m = re.search(r"create_file\([^)]+\)[^\n]+", sdl, re.S)
    assert m, "create_file disappeared from SDL"
    sig = m.group(0)
    assert "file_name: String!" in sig, f"create_file lost positional file_name: {sig}"
    assert "input: CreateFileInput" not in sig, (
        f"create_file regressed to input wrapper — would break nshm-toshi-client: {sig}"
    )


def test_create_file_relation_uses_positional_args(sdl):
    """Sibling mutation also stays positional."""
    m = re.search(r"create_file_relation\([^)]+\)[^\n]+", sdl, re.S)
    assert m, "create_file_relation disappeared from SDL"
    sig = m.group(0)
    assert "file_id: ID!" in sig, f"create_file_relation lost positional file_id: {sig}"
    assert "input: CreateFileRelationInput" not in sig, f"create_file_relation regressed: {sig}"


def test_create_task_relation_uses_positional_args(sdl):
    """create_task_relation matches `(child_id, parent_id)` legacy shape."""
    m = re.search(r"create_task_relation\([^)]+\)[^\n]+", sdl, re.S)
    assert m, "create_task_relation disappeared from SDL"
    sig = m.group(0)
    assert "child_id: ID!" in sig, f"create_task_relation lost positional child_id: {sig}"
    assert "parent_id: ID!" in sig, f"create_task_relation lost positional parent_id: {sig}"
    assert "input: CreateTaskRelationInput" not in sig, f"create_task_relation regressed: {sig}"


# ── Invariant 3: Connection type names match legacy ──────────────────────────


def test_connection_type_names_match_legacy(sdl):
    """Connection types use legacy names — clients embed these in fragments."""
    # Legacy: FileRelationConnection (no plural "s"), TaskTaskRelationConnection (double "Task")
    assert "type FileRelationConnection " in sdl, "FileRelationConnection missing"
    assert "type TaskTaskRelationConnection " in sdl, "TaskTaskRelationConnection missing"
    # POC-original names should be gone
    assert "type FileRelationsConnection " not in sdl, (
        "FileRelationsConnection (plural) regressed into SDL — clients break"
    )
    assert "type TaskRelationsConnection " not in sdl, "TaskRelationsConnection (single Task) regressed into SDL"


# ── Invariant 4: OQ task payloads use `openquake_hazard_task` not `task_result` ──


def test_openquake_hazard_task_payload_field_name(sdl):
    """Create/Update OQ task payloads must expose `openquake_hazard_task`,
    not the POC-original `task_result`. Legacy contract; runzi depends on it.
    """
    for type_name in ("CreateOpenquakeHazardTask", "UpdateOpenquakeHazardTask"):
        m = re.search(rf"type {type_name} \{{[^}}]+\}}", sdl, re.DOTALL)
        assert m, f"{type_name} missing from SDL"
        body = m.group(0)
        assert "openquake_hazard_task:" in body, (
            f"{type_name} missing `openquake_hazard_task` field — legacy contract: {body}"
        )


# ── Invariant 5: chris's audit Problem 2 — specific missing-field regressions ──


def test_labelled_table_relation_has_table_field(sdl):
    """LabelledTableRelation must expose `table` so runzi's
    `tables { table { id } }` query resolves.
    """
    m = re.search(r"type LabelledTableRelation \{[^}]+\}", sdl, re.DOTALL)
    assert m, "LabelledTableRelation missing"
    assert "table: Table" in m.group(0) or "table:" in m.group(0).split("table_type")[0], (
        f"LabelledTableRelation missing `table` field: {m.group(0)}"
    )


def test_create_inversion_solution_input_has_mfd_table_id(sdl):
    """CreateInversionSolutionInput must accept `mfd_table_id` — runzi sends it."""
    m = re.search(r"input CreateInversionSolutionInput \{[^}]+\}", sdl, re.DOTALL)
    assert m, "CreateInversionSolutionInput missing"
    body = m.group(0)
    assert "mfd_table_id:" in body, f"CreateInversionSolutionInput missing mfd_table_id: {body}"
