"""
Tests for GeneralTask — create, list, node lookup, update.

Runs schema.execute_sync() directly against a moto-backed DynamoDB.
All tests in this module share the module-scoped fixture, so created
objects accumulate across tests (same behaviour as existing test suite).

Field and mutation names use snake_case (auto_camel_case=False on schema).
Mutations return payload wrapper types matching the Graphene API shape.
"""

import base64

import pytest

from graphql_api.schema import schema

CREATE_MUTATION = """
mutation CreateTask($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) {
        general_task {
            id
            title
            description
            agent_name
            created
            notes
            subtask_count
            subtask_type
            subtask_result
            model_type
            meta { k v }
            argument_lists { k v }
            swept_arguments
        }
    }
}
"""

UPDATE_MUTATION = """
mutation UpdateTask($input: UpdateGeneralTaskInput!) {
    update_general_task(input: $input) {
        general_task {
            id
            title
            notes
            updated
            subtask_count
        }
    }
}
"""

LIST_QUERY = """
query {
    general_tasks {
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
            agent_name
            subtask_result
            children { total_count }
        }
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

CREATE_TASK_RELATION_MUTATION = """
mutation CreateRelation($child_id: ID!, $parent_id: ID!) {
    create_task_relation(child_id: $child_id, parent_id: $parent_id) {
        ok
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
                "agent_name": "pytest",
                "created": "2024-01-01T00:00:00Z",
                "notes": "initial notes",
                "subtask_count": 3,
                "subtask_type": "INVERSION",
                "subtask_result": "SUCCESS",
                "model_type": "CRUSTAL",
                "meta": [{"k": "env", "v": "ci"}],
                "argument_lists": [
                    {"k": "alpha", "v": ["0.1", "0.2", "0.3"]},
                    {"k": "beta", "v": ["1.0"]},
                ],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_general_task"]["general_task"]


def test_create_returns_id(created_task):
    assert created_task["id"]
    # Relay global IDs are base64("TypeName:raw_id")
    decoded = base64.b64decode(created_task["id"]).decode()
    assert decoded.startswith("GeneralTask:")


def test_create_fields(created_task):
    assert created_task["title"] == "Test task"
    assert created_task["description"] == "A test general task"
    assert created_task["agent_name"] == "pytest"
    assert created_task["created"] == "2024-01-01T00:00:00Z"
    assert created_task["notes"] == "initial notes"
    assert created_task["subtask_count"] == 3
    assert created_task["subtask_type"] == "INVERSION"
    assert created_task["model_type"] == "CRUSTAL"
    assert created_task["meta"] == [{"k": "env", "v": "ci"}]


def test_swept_arguments(created_task):
    # alpha has 3 values → swept; beta has 1 → not swept
    assert created_task["swept_arguments"] == ["alpha"]


def test_list_general_tasks(gql_context, created_task):
    result = schema.execute_sync(LIST_QUERY, context_value=gql_context)
    assert result.errors is None, result.errors

    edges = result.data["general_tasks"]["edges"]
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
    assert node["agent_name"] == "pytest"


def test_update_general_task(gql_context, created_task):
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "task_id": created_task["id"],
                "title": "Updated title",
                "notes": "updated notes",
                "updated": "2024-06-01T00:00:00Z",
                "subtask_count": 5,
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors

    updated = result.data["update_general_task"]["general_task"]
    assert updated["id"] == created_task["id"]
    assert updated["title"] == "Updated title"
    assert updated["notes"] == "updated notes"
    assert updated["updated"] == "2024-06-01T00:00:00Z"
    assert updated["subtask_count"] == 5


def test_update_preserves_id(gql_context, created_task):
    """Update must not change the relay global ID."""
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "task_id": created_task["id"],
                "notes": "another update",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["update_general_task"]["general_task"]["id"] == created_task["id"]


def test_subtask_result_field(created_task):
    """subtask_result is stored and returned as an EventResult enum value."""
    assert created_task["subtask_result"] == "SUCCESS"


def test_children_total_count_zero(gql_context, created_task):
    """children.total_count is 0 when no child tasks have been linked."""
    result = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created_task["id"]}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["children"]["total_count"] == 0


def test_children_total_count_after_relation(gql_context, created_task):
    """children.total_count increments after a task relation is created."""
    child_result = schema.execute_sync(
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
    assert child_result.errors is None, child_result.errors
    child_id = child_result.data["create_automation_task"]["task_result"]["id"]

    rel_result = schema.execute_sync(
        CREATE_TASK_RELATION_MUTATION,
        variable_values={"parent_id": created_task["id"], "child_id": child_id},
        context_value=gql_context,
    )
    assert rel_result.errors is None, rel_result.errors

    result = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created_task["id"]}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["children"]["total_count"] == 1


def test_unknown_enum_value_does_not_crash(gql_context):
    """from_dict must survive unknown enum values in production data (returns None, not an error)."""
    from data.dynamo import create_thing

    raw = create_thing(
        gql_context["dynamodb"],
        "GeneralTask",
        {
            "title": "enum resilience test",
            "subtask_type": "future_unknown_type",
            "subtask_result": "future_unknown_result",
            "model_type": "future_unknown_model",
        },
    )
    import base64

    gid = base64.b64encode(f"GeneralTask:{raw['object_id']}".encode()).decode()
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": gid}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["title"] == "enum resilience test"
    assert node["subtask_result"] is None
