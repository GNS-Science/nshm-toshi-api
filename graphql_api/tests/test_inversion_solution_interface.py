"""
Tests for InversionSolutionInterface fragment queries.

Exercises the `... on InversionSolutionInterface { ... }` pattern used by
weka clients, verifying that mfd_table_id, mfd_table, hazard_table_id,
relations { total_count }, tables, file_name, and created all resolve
correctly through the interface fragment on InversionSolution and
ScaledInversionSolution nodes.
"""

import base64

import pytest

from graphql_api.schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

# Mirrors the weka query pattern that was broken before InversionSolutionInterface
# was added to the Strawberry POC schema.
INTERFACE_NODE_QUERY = """
query GetNodeViaInterface($id: ID!) {
    node(id: $id) {
        id
        __typename
        ... on InversionSolutionInterface {
            file_name
            created
            mfd_table_id
            mfd_table { id }
            hazard_table_id
            tables {
                table_id
                table_type
            }
            relations {
                total_count
            }
            produced_by {
                ... on RuptureGenerationTask { id }
                ... on AutomationTask { id }
            }
        }
    }
}
"""

CREATE_TABLE_MUTATION = """
mutation CreateTable($input: CreateTableInput!) {
    create_table(input: $input) {
        ok
        table { id }
    }
}
"""

CREATE_IS_MUTATION = """
mutation CreateIS($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) {
        ok
        inversion_solution { id }
    }
}
"""

CREATE_SIS_MUTATION = """
mutation CreateSIS($input: CreateScaledInversionSolutionInput!) {
    create_scaled_inversion_solution(input: $input) {
        ok
        solution { id }
    }
}
"""

CREATE_FILE_RELATION_MUTATION = """
mutation CreateFileRelation($file_id: ID!, $role: FileRole!, $thing_id: ID!) {
    create_file_relation(file_id: $file_id, role: $role, thing_id: $thing_id) {
        ok
    }
}
"""

CREATE_AUTOMATION_TASK_MUTATION = """
mutation CreateTask($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) {
        task_result { id }
    }
}
"""


# ── Seed helpers ──────────────────────────────────────────────────────────────


def _seed_rgt(gql_context) -> str:
    from graphql_api.data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2024-01-01T00:00:00Z"},
    )
    return base64.b64encode(f"RuptureGenerationTask:{data['object_id']}".encode()).decode()


def _seed_mfd_table(gql_context, rgt_id: str) -> str:
    result = schema.execute_sync(
        CREATE_TABLE_MUTATION,
        variable_values={
            "input": {
                "object_id": rgt_id,
                "table_type": "MFD_CURVES_V2",
                "created": "2024-01-01T00:00:00Z",
                "column_headers": ["mag", "rate"],
                "column_types": ["double", "double"],
                "rows": [["7.0", "1e-5"], ["7.5", "5e-6"]],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_table"]["table"]["id"]


def _seed_automation_task(gql_context) -> str:
    result = schema.execute_sync(
        CREATE_AUTOMATION_TASK_MUTATION,
        variable_values={
            "input": {
                "state": "DONE",
                "result": "SUCCESS",
                "task_type": "INVERSION",
                "created": "2024-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_automation_task"]["task_result"]["id"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    return _seed_rgt(gql_context)


@pytest.fixture(scope="module")
def mfd_table_id(gql_context, rgt_id):
    return _seed_mfd_table(gql_context, rgt_id)


@pytest.fixture(scope="module")
def is_with_mfd_table(gql_context, rgt_id, mfd_table_id):
    """InversionSolution that has one MFD_CURVES_V2 table entry."""
    result = schema.execute_sync(
        CREATE_IS_MUTATION,
        variable_values={
            "input": {
                "file_name": "is_with_mfd.zip",
                "produced_by": rgt_id,
                "md5_digest": "aabbccdd",
                "file_size": 1024,
                "created": "2024-06-01T00:00:00Z",
                "tables": [
                    {"table_id": mfd_table_id, "table_type": "MFD_CURVES_V2", "label": "mfd"}
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution"]["inversion_solution"]["id"]


@pytest.fixture(scope="module")
def sis_with_mfd_table(gql_context, is_with_mfd_table):
    """ScaledInversionSolution pointing to is_with_mfd_table."""
    result = schema.execute_sync(
        CREATE_SIS_MUTATION,
        variable_values={
            "input": {
                "file_name": "sis_iface_test.zip",
                "source_solution": is_with_mfd_table,
                "md5_digest": "eeff0011",
                "file_size": 512,
                "created": "2024-06-02T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_scaled_inversion_solution"]["solution"]["id"]


# ── Tests: InversionSolution via interface fragment ───────────────────────────


def test_interface_fragment_resolves_file_name(gql_context, is_with_mfd_table):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "InversionSolution"
    assert node["file_name"] == "is_with_mfd.zip"
    assert node["created"] == "2024-06-01T00:00:00Z"


def test_mfd_table_id_resolves(gql_context, is_with_mfd_table, mfd_table_id):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["mfd_table_id"] == mfd_table_id


def test_mfd_table_resolves(gql_context, is_with_mfd_table, mfd_table_id):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["mfd_table"]["id"] == mfd_table_id


def test_hazard_table_id_null_when_no_hazard_table(gql_context, is_with_mfd_table):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["hazard_table_id"] is None


def test_tables_via_interface_fragment(gql_context, is_with_mfd_table, mfd_table_id):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    tables = result.data["node"]["tables"]
    assert len(tables) == 1
    assert tables[0]["table_id"] == mfd_table_id
    assert tables[0]["table_type"] == "MFD_CURVES_V2"


def test_produced_by_via_interface_fragment(gql_context, is_with_mfd_table, rgt_id):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    pb = result.data["node"]["produced_by"]
    assert pb is not None
    assert pb["id"] == rgt_id


def test_relations_total_count_zero_when_no_relations(gql_context, is_with_mfd_table):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    rels = result.data["node"]["relations"]
    assert rels is not None
    assert rels["total_count"] == 0


def test_relations_total_count_after_create_file_relation(gql_context, is_with_mfd_table):
    task_id = _seed_automation_task(gql_context)
    rel_result = schema.execute_sync(
        CREATE_FILE_RELATION_MUTATION,
        variable_values={"thing_id": task_id, "file_id": is_with_mfd_table, "role": "READ"},
        context_value=gql_context,
    )
    assert rel_result.errors is None, rel_result.errors
    assert rel_result.data["create_file_relation"]["ok"] is True

    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": is_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["relations"]["total_count"] == 1


# ── Tests: ScaledInversionSolution via interface fragment ─────────────────────


def test_scaled_typename_via_interface_fragment(gql_context, sis_with_mfd_table):
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": sis_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "ScaledInversionSolution"
    assert node["file_name"] == "sis_iface_test.zip"


def test_scaled_mfd_table_null_when_no_tables(gql_context, sis_with_mfd_table):
    """ScaledInversionSolution created without tables → mfd_table_id is null."""
    result = schema.execute_sync(
        INTERFACE_NODE_QUERY, variable_values={"id": sis_with_mfd_table}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["mfd_table_id"] is None
    assert node["mfd_table"] is None
