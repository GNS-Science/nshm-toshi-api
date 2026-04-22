"""
Tests for GeneralTask — create, list, node lookup, update.

Runs schema.execute_sync() directly against a moto-backed DynamoDB.
All tests in this module share the module-scoped fixture, so created
objects accumulate across tests (same behaviour as existing test suite).
"""
import base64

import pytest

from schema import schema


CREATE_MUTATION = """
mutation CreateTask($input: CreateGeneralTaskInput!) {
    createGeneralTask(input: $input) {
        id
        title
        description
        agentName
        created
        notes
        subtaskCount
        subtaskType
        modelType
        meta { k v }
        argumentLists { k v }
        sweptArguments
    }
}
"""

UPDATE_MUTATION = """
mutation UpdateTask($input: UpdateGeneralTaskInput!) {
    updateGeneralTask(input: $input) {
        id
        title
        notes
        updated
        subtaskCount
    }
}
"""

LIST_QUERY = """
query {
    generalTasks {
        edges {
            node {
                id
                title
            }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on GeneralTask {
            title
            description
            agentName
        }
    }
}
"""


@pytest.fixture(scope="module")
def created_task(gql_context):
    """Create one GeneralTask and return the result dict — shared across tests."""
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "title": "Test task",
                "description": "A test general task",
                "agentName": "pytest",
                "created": "2024-01-01T00:00:00Z",
                "notes": "initial notes",
                "subtaskCount": 3,
                "subtaskType": "INVERSION",
                "modelType": "CRUSTAL",
                "meta": [{"k": "env", "v": "ci"}],
                "argumentLists": [
                    {"k": "alpha", "v": ["0.1", "0.2", "0.3"]},
                    {"k": "beta", "v": ["1.0"]},
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["createGeneralTask"]


def test_create_returns_id(created_task):
    assert created_task["id"]
    # Relay global IDs are base64("TypeName:raw_id")
    decoded = base64.b64decode(created_task["id"]).decode()
    assert decoded.startswith("GeneralTask:")


def test_create_fields(created_task):
    assert created_task["title"] == "Test task"
    assert created_task["description"] == "A test general task"
    assert created_task["agentName"] == "pytest"
    assert created_task["created"] == "2024-01-01T00:00:00Z"
    assert created_task["notes"] == "initial notes"
    assert created_task["subtaskCount"] == 3
    assert created_task["subtaskType"] == "INVERSION"
    assert created_task["modelType"] == "CRUSTAL"
    assert created_task["meta"] == [{"k": "env", "v": "ci"}]


def test_swept_arguments(created_task):
    # alpha has 3 values → swept; beta has 1 → not swept
    assert created_task["sweptArguments"] == ["alpha"]


def test_list_general_tasks(gql_context, created_task):
    result = schema.execute_sync(LIST_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors

    edges = result.data["generalTasks"]["edges"]
    assert len(edges) >= 1
    ids = [e["node"]["id"] for e in edges]
    assert created_task["id"] in ids


def test_node_lookup(gql_context, created_task):
    result = schema.execute_sync(
        NODE_QUERY,
        variable_values={"id": created_task["id"]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors

    node = result.data["node"]
    assert node["id"] == created_task["id"]
    assert node["title"] == "Test task"
    assert node["description"] == "A test general task"
    assert node["agentName"] == "pytest"


def test_update_general_task(gql_context, created_task):
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "taskId": created_task["id"],
                "title": "Updated title",
                "notes": "updated notes",
                "updated": "2024-06-01T00:00:00Z",
                "subtaskCount": 5,
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors

    updated = result.data["updateGeneralTask"]
    assert updated["id"] == created_task["id"]
    assert updated["title"] == "Updated title"
    assert updated["notes"] == "updated notes"
    assert updated["updated"] == "2024-06-01T00:00:00Z"
    assert updated["subtaskCount"] == 5


def test_update_preserves_id(gql_context, created_task):
    """Update must not change the relay global ID."""
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "taskId": created_task["id"],
                "notes": "another update",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["updateGeneralTask"]["id"] == created_task["id"]
