"""
Tests for Table — create, node lookup, mfd_table resolver on InversionSolution.
"""

import base64

import pytest

from schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_TABLE_MUTATION = """
mutation CreateTable($input: CreateTableInput!) {
    create_table(input: $input) {
        ok
        table {
            id
            object_id
            created
            column_headers
            column_types
            rows
            meta { k v }
            dimensions { k v }
            table_type
        }
    }
}
"""

NODE_QUERY = """
query GetTable($id: ID!) {
    node(id: $id) {
        id
        ... on Table {
            object_id
            column_headers
            column_types
            rows
            meta { k v }
            dimensions { k v }
            table_type
        }
    }
}
"""

CREATE_IS_MUTATION = """
mutation CreateIS($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) {
        ok
        inversion_solution {
            id
            mfd_table { id }
        }
    }
}
"""


# ── Seed helpers ──────────────────────────────────────────────────────────────


def _seed_rgt(gql_context) -> str:
    from data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2024-01-01T00:00:00Z"},
    )
    return base64.b64encode(f"RuptureGenerationTask:{data['object_id']}".encode()).decode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def task_id(gql_context):
    """A RuptureGenerationTask ID to use as object_id for the table."""
    return _seed_rgt(gql_context)


@pytest.fixture(scope="module")
def created_table(gql_context, task_id):
    result = schema.execute_sync(
        CREATE_TABLE_MUTATION,
        variable_values={
            "input": {
                "object_id": task_id,
                "created": "2024-06-01T00:00:00Z",
                "column_headers": ["mag", "rate"],
                "column_types": ["double", "double"],
                "rows": [["6.0", "0.01"], ["7.0", "0.001"]],
                "meta": [{"k": "source", "v": "opensha"}],
                "table_type": "MFD_CURVES_V2",
                "dimensions": [{"k": "iml_periods", "v": ["0", "0.1", "0.2"]}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_table"]["table"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_returns_id(created_table):
    gid = created_table["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("Table:"), decoded


def test_create_ok(gql_context, task_id):
    result = schema.execute_sync(
        CREATE_TABLE_MUTATION,
        variable_values={
            "input": {
                "object_id": task_id,
                "column_headers": ["a"],
                "rows": [["1"]],
                "table_type": "HAZARD_GRIDDED",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_table"]["ok"] is True


def test_fields(created_table):
    t = created_table
    assert t["column_headers"] == ["mag", "rate"]
    assert t["column_types"] == ["double", "double"]
    assert t["rows"] == [["6.0", "0.01"], ["7.0", "0.001"]]
    assert t["meta"] == [{"k": "source", "v": "opensha"}]
    assert t["table_type"] == "MFD_CURVES_V2"


def test_dimensions(created_table):
    dims = created_table["dimensions"]
    assert len(dims) == 1
    assert dims[0]["k"] == "iml_periods"
    assert dims[0]["v"] == ["0", "0.1", "0.2"]


def test_node_lookup(created_table, gql_context):
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": created_table["id"]}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["column_headers"] == ["mag", "rate"]
    assert node["rows"] == [["6.0", "0.01"], ["7.0", "0.001"]]
    assert node["table_type"] == "MFD_CURVES_V2"
    assert node["dimensions"][0]["k"] == "iml_periods"


# ── name field (COVERAGE_GAPS.md gap 7) ───────────────────────────────────────

CREATE_TABLE_WITH_NAME_MUTATION = """
mutation CreateTable($input: CreateTableInput!) {
    create_table(input: $input) {
        ok
        table { id name table_type }
    }
}
"""

NODE_NAME_QUERY = """
query GetTable($id: ID!) {
    node(id: $id) {
        id
        ... on Table { name table_type }
    }
}
"""


def test_create_table_with_name(gql_context, task_id):
    """The name input field round-trips to Table.name."""
    result = schema.execute_sync(
        CREATE_TABLE_WITH_NAME_MUTATION,
        variable_values={
            "input": {
                "object_id": task_id,
                "name": "MFD Curves v2",
                "table_type": "MFD_CURVES_V2",
                "column_headers": ["mag"],
                "rows": [["7.0"]],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    table = result.data["create_table"]["table"]
    assert table["name"] == "MFD Curves v2"


def test_table_node_lookup_returns_name(gql_context, task_id):
    create_result = schema.execute_sync(
        CREATE_TABLE_WITH_NAME_MUTATION,
        variable_values={
            "input": {
                "object_id": task_id,
                "name": "Hazard Sites Grid",
                "table_type": "HAZARD_SITES",
            }
        },
        context_value=gql_context,
    )
    assert create_result.errors is None, create_result.errors
    table_id = create_result.data["create_table"]["table"]["id"]

    result = schema.execute_sync(
        NODE_NAME_QUERY, variable_values={"id": table_id}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["name"] == "Hazard Sites Grid"


def test_mfd_table_on_inversion_solution(gql_context, created_table):
    """InversionSolution.mfd_table resolves when a MFD_CURVES_V2 table entry is linked."""
    rgt_id = _seed_rgt(gql_context)
    result = schema.execute_sync(
        CREATE_IS_MUTATION,
        variable_values={
            "input": {
                "file_name": "is_with_mfd.zip",
                "produced_by": rgt_id,
                "md5_digest": "12345678",
                "file_size": 512,
                "created": "2024-06-01T00:00:00Z",
                "tables": [
                    {
                        "table_id": created_table["id"],
                        "table_type": "MFD_CURVES_V2",
                        "label": "mfd",
                    }
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    is_ = result.data["create_inversion_solution"]["inversion_solution"]
    assert is_["mfd_table"] is not None
    assert is_["mfd_table"]["id"] == created_table["id"]
