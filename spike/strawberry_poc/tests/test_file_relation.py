"""Tests for file relations — linking ToshiFiles to tasks."""


import pytest

from schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_AUTOMATION_TASK_MUTATION = """
mutation CreateTask($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) {
        task_result {
            id
        }
    }
}
"""

CREATE_FILE_MUTATION = """
mutation CreateFile($input: CreateFileInput!) {
    create_file(input: $input) {
        ok
        file_result { id }
    }
}
"""

CREATE_FILE_RELATION_MUTATION = """
mutation CreateFileRelation($input: CreateFileRelationInput!) {
    create_file_relation(input: $input) {
        ok
    }
}
"""

TASK_FILES_QUERY = """
query GetTask($id: ID!) {
    node(id: $id) {
        id
        ... on AutomationTask {
            files {
                edges {
                    node {
                        role
                        file {
                            ... on File { id }
                        }
                    }
                }
            }
        }
    }
}
"""


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def task_id(gql_context):
    result = schema.execute_sync(
        CREATE_AUTOMATION_TASK_MUTATION,
        variable_values={
            "input": {
                "state": "UNDEFINED",
                "result": "UNDEFINED",
                "task_type": "INVERSION",
                "created": "2024-08-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_automation_task"]["task_result"]["id"]


@pytest.fixture(scope="module")
def file_id(gql_context):
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "output_data.zip",
                "md5_digest": "99aabbcc",
                "file_size": 2048,
                "created": "2024-08-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_file"]["file_result"]["id"]


@pytest.fixture(scope="module")
def created_relation(gql_context, task_id, file_id):
    result = schema.execute_sync(
        CREATE_FILE_RELATION_MUTATION,
        variable_values={"input": {"thing_id": task_id, "file_id": file_id, "role": "READ"}},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_file_relation"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_file_relation_ok(created_relation):
    assert created_relation["ok"] is True


def test_file_appears_in_task_files(gql_context, task_id, file_id, created_relation):
    result = schema.execute_sync(TASK_FILES_QUERY, variable_values={"id": task_id}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    edges = node["files"]["edges"]
    assert len(edges) >= 1
    linked_ids = [e["node"]["file"]["id"] for e in edges if e["node"]["file"]]
    assert file_id in linked_ids, f"{file_id} not in {linked_ids}"


def test_file_relation_role(gql_context, task_id, created_relation):
    result = schema.execute_sync(TASK_FILES_QUERY, variable_values={"id": task_id}, context_value=gql_context)
    assert result.errors is None, result.errors
    edges = result.data["node"]["files"]["edges"]
    roles = [e["node"]["role"] for e in edges]
    assert "READ" in roles
