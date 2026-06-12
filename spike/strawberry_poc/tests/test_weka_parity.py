"""Weka client parity tests.

Locks in three wire-format fixes that real production clients depend on:

  1. The file type is named `File` in SDL (not `ToshiFile`) — weka and
     nzshm-model query `... on File`.
  2. `nodes(...)` returns a `NodeFilter` payload type (not `NodeFilterPayload`)
     — weka's Relay codegen references `concreteType: "NodeFilter"`.
  3. `column_types` is `[RowItemType]` — runzi mutations declare
     `$column_types: [RowItemType]!`.

Also covers the `inversion_solution` resolver on AutomationTask /
RuptureGenerationTask / OpenquakeHazardTask, which weka queries on
GeneralTask children pages.
"""

import base64

import pytest

from schema import schema


def _gid(typename: str, raw_id: str) -> str:
    return base64.b64encode(f"{typename}:{raw_id}".encode()).decode()


# ── 1. File SDL name ──────────────────────────────────────────────────────────


FILE_TYPENAME_QUERY = """
query GetFile($id: ID!) {
    node(id: $id) {
        __typename
        ... on File {
            id
            file_name
        }
    }
}
"""

CREATE_FILE_MUTATION = """
mutation CreateFile($file_name: String!, $md5_digest: String!, $file_size: BigInt!, $created: DateTime = null, $meta: [KeyValuePairInput!] = null) {
    create_file(file_name: $file_name, md5_digest: $md5_digest, file_size: $file_size, created: $created, meta: $meta) {
        ok
        file_result { id file_name }
    }
}
"""


def test_file_sdl_typename(gql_context):
    res = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={"file_name": "weka.zip", "md5_digest": "abc", "file_size": 100},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    fid = res.data["create_file"]["file_result"]["id"]

    res2 = schema.execute_sync(FILE_TYPENAME_QUERY, variable_values={"id": fid}, context_value=gql_context)
    assert res2.errors is None, res2.errors
    assert res2.data["node"]["__typename"] == "File"
    assert res2.data["node"]["file_name"] == "weka.zip"


def test_file_introspection_has_no_toshifile():
    sdl = schema.as_str()
    assert "type File implements" in sdl
    assert "type ToshiFile " not in sdl
    assert "type ToshiFile\n" not in sdl


# ── 2. NodeFilter SDL name ────────────────────────────────────────────────────


NODES_QUERY = """
query Nodes($id_in: [ID!]!) {
    nodes(id_in: $id_in) {
        ok
        result {
            edges { node { __typename ... on Node { id } } }
        }
    }
}
"""


def test_nodes_payload_sdl_name():
    sdl = schema.as_str()
    assert "type NodeFilter " in sdl or "type NodeFilter\n" in sdl
    assert "type NodeFilterPayload" not in sdl


def test_nodes_works(gql_context):
    create_res = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={"file_name": "nodes-test.zip", "md5_digest": "abc", "file_size": 100},
        context_value=gql_context,
    )
    fid = create_res.data["create_file"]["file_result"]["id"]
    res = schema.execute_sync(NODES_QUERY, variable_values={"id_in": [fid]}, context_value=gql_context)
    assert res.errors is None, res.errors
    assert res.data["nodes"]["ok"] is True


# ── 3. RowItemType enum ───────────────────────────────────────────────────────


def test_rowitemtype_enum_in_sdl():
    sdl = schema.as_str()
    assert "enum RowItemType" in sdl
    for v in ("integer", "double", "string", "boolean"):
        assert v in sdl, f"{v} missing from RowItemType"


CREATE_TABLE_WITH_TYPED_COLUMNS = """
mutation CreateTable($input: CreateTableInput!) {
    create_table(input: $input) {
        table { id column_types }
    }
}
"""


@pytest.fixture
def task_id(gql_context):
    res = schema.execute_sync(
        """
        mutation Create($input: CreateAutomationTaskInput!) {
            create_automation_task(input: $input) { task_result { id } }
        }
        """,
        variable_values={
            "input": {
                "state": "UNDEFINED",
                "result": "UNDEFINED",
                "task_type": "INVERSION",
                "created": "2026-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_automation_task"]["task_result"]["id"]


def test_column_types_accepts_rowitemtype_enum(gql_context, task_id):
    res = schema.execute_sync(
        CREATE_TABLE_WITH_TYPED_COLUMNS,
        variable_values={
            "input": {
                "object_id": task_id,
                "table_type": "MFD_CURVES_V2",
                "column_headers": ["mag", "rate"],
                "column_types": ["double", "double"],
                "rows": [["7.0", "1e-5"]],
            }
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    assert res.data["create_table"]["table"]["column_types"] == ["double", "double"]


def test_column_types_rejects_invalid_enum(gql_context, task_id):
    res = schema.execute_sync(
        CREATE_TABLE_WITH_TYPED_COLUMNS,
        variable_values={
            "input": {
                "object_id": task_id,
                "table_type": "MFD_CURVES_V2",
                "column_headers": ["x"],
                "column_types": ["float"],  # legacy/runzi never used this name
                "rows": [["1.0"]],
            }
        },
        context_value=gql_context,
    )
    assert res.errors is not None
    assert "RowItemType" in str(res.errors[0])


# ── 4. inversion_solution on AutomationTask family ─────────────────────────────


CREATE_IS_MUTATION = """
mutation CreateIS($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) {
        ok
        inversion_solution { id }
    }
}
"""

CREATE_FILE_RELATION = """
mutation CreateRel($file_id: ID!, $role: FileRole!, $thing_id: ID!) {
    create_file_relation(file_id: $file_id, role: $role, thing_id: $thing_id) { ok }
}
"""

TASK_IS_QUERY = """
query GetTask($id: ID!) {
    node(id: $id) {
        ... on AutomationTask {
            inversion_solution {
                __typename
                ... on InversionSolution { id }
            }
        }
    }
}
"""


def test_automation_task_inversion_solution_resolves(gql_context, task_id):
    is_res = schema.execute_sync(
        CREATE_IS_MUTATION,
        variable_values={
            "input": {
                "file_name": "is.zip",
                "produced_by": task_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert is_res.errors is None, is_res.errors
    is_id = is_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    rel_res = schema.execute_sync(
        CREATE_FILE_RELATION,
        variable_values={"thing_id": task_id, "file_id": is_id, "role": "WRITE"},
        context_value=gql_context,
    )
    assert rel_res.errors is None, rel_res.errors

    q = schema.execute_sync(TASK_IS_QUERY, variable_values={"id": task_id}, context_value=gql_context)
    assert q.errors is None, q.errors
    sol = q.data["node"]["inversion_solution"]
    assert sol is not None
    assert sol["__typename"] == "InversionSolution"
    assert sol["id"] == is_id


def test_automation_task_inversion_solution_null_without_write_relation(gql_context):
    # Brand-new task with no file relations → inversion_solution is None
    create = schema.execute_sync(
        """
        mutation Create($input: CreateAutomationTaskInput!) {
            create_automation_task(input: $input) { task_result { id } }
        }
        """,
        variable_values={
            "input": {
                "state": "UNDEFINED",
                "result": "UNDEFINED",
                "task_type": "INVERSION",
                "created": "2026-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    tid = create.data["create_automation_task"]["task_result"]["id"]
    q = schema.execute_sync(TASK_IS_QUERY, variable_values={"id": tid}, context_value=gql_context)
    assert q.errors is None, q.errors
    assert q.data["node"]["inversion_solution"] is None


def test_inversion_solution_union_in_sdl():
    sdl = schema.as_str()
    assert (
        "union InversionSolutionUnion = "
        "InversionSolution | ScaledInversionSolution | "
        "AggregateInversionSolution | TimeDependentInversionSolution"
    ) in sdl
