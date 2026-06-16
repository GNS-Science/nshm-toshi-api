"""
Tests for AutomationTask — create, node lookup, update mutation, ES re-index.

Covers COVERAGE_GAPS.md gaps 1 (update_automation_task) and 10 (ES re-index on update).
The update_automation_task mutation was wired in Phase A1.
"""

import base64

import pytest

from graphql_api.schema import schema

CREATE_MUTATION = """
mutation CreateTask($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) {
        task_result {
            id
            state
            result
            task_type
            created
            duration
            arguments { k v }
            environment { k v }
            metrics { k v }
        }
    }
}
"""

UPDATE_MUTATION = """
mutation UpdateTask($input: UpdateAutomationTaskInput!) {
    update_automation_task(input: $input) {
        task_result {
            id
            state
            result
            duration
            metrics { k v }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on AutomationTask {
            state
            result
            duration
            metrics { k v }
        }
    }
}
"""


@pytest.fixture(scope="module")
def created_task(gql_context):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "state": "SCHEDULED",
                "result": "UNDEFINED",
                "task_type": "INVERSION",
                "created": "2024-01-01T00:00:00Z",
                "duration": 0.0,
                "arguments": [{"k": "alpha", "v": "0.1"}],
                "environment": [{"k": "host", "v": "ci"}],
                "metrics": [{"k": "iters", "v": "10"}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_automation_task"]["task_result"]


def test_create_returns_id(created_task):
    assert created_task["id"]
    decoded = base64.b64decode(created_task["id"]).decode()
    assert decoded.startswith("AutomationTask:")


def test_create_fields(created_task):
    assert created_task["state"] == "SCHEDULED"
    assert created_task["result"] == "UNDEFINED"
    assert created_task["task_type"] == "INVERSION"
    assert created_task["created"] == "2024-01-01T00:00:00Z"
    assert created_task["arguments"] == [{"k": "alpha", "v": "0.1"}]
    assert created_task["environment"] == [{"k": "host", "v": "ci"}]
    assert created_task["metrics"] == [{"k": "iters", "v": "10"}]


def test_update_state_and_result(gql_context, created_task):
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "task_id": created_task["id"],
                "state": "DONE",
                "result": "SUCCESS",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    updated = result.data["update_automation_task"]["task_result"]
    assert updated["state"] == "DONE"
    assert updated["result"] == "SUCCESS"

    node_result = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created_task["id"]}, context_value=gql_context
    )
    assert node_result.errors is None, node_result.errors
    assert node_result.data["node"]["state"] == "DONE"
    assert node_result.data["node"]["result"] == "SUCCESS"


def test_update_duration_and_metrics(gql_context, created_task):
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "task_id": created_task["id"],
                "duration": 123.45,
                "metrics": [{"k": "iters", "v": "100"}, {"k": "rmse", "v": "0.02"}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    updated = result.data["update_automation_task"]["task_result"]
    assert updated["duration"] == 123.45
    assert {"k": "rmse", "v": "0.02"} in updated["metrics"]


def test_update_preserves_id(gql_context, created_task):
    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={"input": {"task_id": created_task["id"], "duration": 999.0}},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["update_automation_task"]["task_result"]["id"] == created_task["id"]


def test_update_triggers_es_reindex(gql_context, created_task, monkeypatch):
    """Updating an AutomationTask must trigger ES re-indexing (gap 10)."""
    from graphql_api.data import dynamo as dynamo_mod

    calls = []

    def fake_index(doc_id, body):
        calls.append((doc_id, body))

    monkeypatch.setattr(dynamo_mod, "index_document", fake_index)

    result = schema.execute_sync(
        UPDATE_MUTATION,
        variable_values={
            "input": {
                "task_id": created_task["id"],
                "state": "STARTED",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors

    raw_id = base64.b64decode(created_task["id"]).decode().split(":")[1]
    expected_doc_id = f"ThingData_{raw_id}"
    matching = [c for c in calls if c[0] == expected_doc_id]
    assert matching, f"index_document was not called with {expected_doc_id}; calls: {calls}"
    assert matching[0][1].get("state") == "started"
