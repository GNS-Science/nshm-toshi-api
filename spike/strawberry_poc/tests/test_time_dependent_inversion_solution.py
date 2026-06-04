"""
Tests for TimeDependentInversionSolution — produced_by, source_solution, predecessors.
"""

import base64

import pytest

from schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_MUTATION = """
mutation CreateTimeDependent($input: CreateTimeDependentInversionSolutionInput!) {
    create_time_dependent_inversion_solution(input: $input) {
        ok
        solution {
            id
            file_name
            md5_digest
            file_size
            created
            produced_by {
                ... on AutomationTask { id }
                ... on RuptureGenerationTask { id }
            }
            source_solution {
                ... on InversionSolution { id }
            }
            predecessors {
                id
                depth
                typename
                relationship
            }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on TimeDependentInversionSolution {
            file_name
            produced_by {
                ... on AutomationTask { id }
                ... on RuptureGenerationTask { id }
            }
            source_solution {
                ... on InversionSolution { id }
            }
            predecessors {
                id
                depth
                relationship
            }
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


def _seed_automation_task(gql_context) -> str:
    from data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "AutomationTask",
        {
                "state": "done",
                "result": "success",
                "task_type": "time_dependent_solution",
                "created": "2024-01-01T00:00:00Z",
            },
    )
    return base64.b64encode(f"AutomationTask:{data['object_id']}".encode()).decode()


def _seed_inversion_solution(gql_context, rgt_id: str) -> str:
    result = schema.execute_sync(
        """
        mutation($input: CreateInversionSolutionInput!) {
            create_inversion_solution(input: $input) {
                ok
                inversion_solution { id }
            }
        }
        """,
        variable_values={
            "input": {
                "file_name": "upstream_td.zip",
                "produced_by": rgt_id,
                "md5_digest": "11223344",
                "file_size": 2048,
                "created": "2024-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution"]["inversion_solution"]["id"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    return _seed_rgt(gql_context)


@pytest.fixture(scope="module")
def automation_task_id(gql_context):
    return _seed_automation_task(gql_context)


@pytest.fixture(scope="module")
def source_solution_id(gql_context, rgt_id):
    return _seed_inversion_solution(gql_context, rgt_id)


@pytest.fixture(scope="module")
def created_td(gql_context, automation_task_id, source_solution_id):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "time_dependent_v1.zip",
                "source_solution": source_solution_id,
                "produced_by": automation_task_id,
                "md5_digest": "feedface",
                "file_size": 1024,
                "created": "2024-04-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_time_dependent_inversion_solution"]["solution"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_returns_id(created_td):
    gid = created_td["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("TimeDependentInversionSolution:"), decoded


def test_fields(created_td):
    s = created_td
    assert s["file_name"] == "time_dependent_v1.zip"
    assert s["md5_digest"] == "feedface"
    assert s["file_size"] == 1024
    assert s["created"] == "2024-04-01T00:00:00Z"


def test_produced_by(created_td, automation_task_id):
    pb = created_td["produced_by"]
    assert pb is not None
    assert pb["id"] == automation_task_id


def test_source_solution(created_td, source_solution_id):
    ss = created_td["source_solution"]
    assert ss is not None
    assert ss["id"] == source_solution_id


def test_node_lookup(created_td, gql_context, automation_task_id, source_solution_id):
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": created_td["id"]}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["file_name"] == "time_dependent_v1.zip"
    assert node["produced_by"]["id"] == automation_task_id
    assert node["source_solution"]["id"] == source_solution_id


def test_with_predecessors(gql_context, automation_task_id, source_solution_id):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "td_with_pred.zip",
                "source_solution": source_solution_id,
                "produced_by": automation_task_id,
                "md5_digest": "beefdead",
                "file_size": 512,
                "created": "2024-04-02T00:00:00Z",
                "predecessors": [{"id": source_solution_id, "depth": -1}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    preds = result.data["create_time_dependent_inversion_solution"]["solution"]["predecessors"]
    assert len(preds) == 1
    assert preds[0]["id"] == source_solution_id
    assert preds[0]["depth"] == -1
    assert preds[0]["relationship"] == "parent"
