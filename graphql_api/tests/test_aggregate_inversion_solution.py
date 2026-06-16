"""
Tests for AggregateInversionSolution — source_solutions array, common_rupture_set,
aggregation_fn, produced_by, predecessors.
"""

import base64

import pytest

from graphql_api.schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_MUTATION = """
mutation CreateAggregate($input: CreateAggregateInversionSolutionInput!) {
    create_aggregate_inversion_solution(input: $input) {
        ok
        solution {
            id
            file_name
            md5_digest
            file_size
            created
            aggregation_fn
            produced_by {
                ... on AutomationTask { id }
                ... on RuptureGenerationTask { id }
            }
            source_solutions {
                ... on InversionSolution { id }
                ... on ScaledInversionSolution { id }
            }
            common_rupture_set { id }
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
        ... on AggregateInversionSolution {
            file_name
            aggregation_fn
            produced_by {
                ... on AutomationTask { id }
                ... on RuptureGenerationTask { id }
            }
            source_solutions {
                ... on InversionSolution { id }
            }
            common_rupture_set { id }
        }
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


def _seed_automation_task(gql_context) -> str:
    from graphql_api.data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "AutomationTask",
        {"state": "done", "result": "success", "task_type": "aggregate_solution", "created": "2024-01-01T00:00:00Z"},
    )
    return base64.b64encode(f"AutomationTask:{data['object_id']}".encode()).decode()


def _seed_inversion_solution(gql_context, rgt_id: str, label: str = "upstream.zip") -> str:
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
                "file_name": label,
                "produced_by": rgt_id,
                "md5_digest": "aabbccdd",
                "file_size": 1024,
                "created": "2024-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution"]["inversion_solution"]["id"]


def _seed_rupture_set(gql_context, label: str = "rupture_set.zip") -> str:
    from graphql_api.data.dynamo import create_file

    data = create_file(gql_context["dynamodb"], "RuptureSet", {"file_name": label})
    return base64.b64encode(f"RuptureSet:{data['object_id']}".encode()).decode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    return _seed_rgt(gql_context)


@pytest.fixture(scope="module")
def automation_task_id(gql_context):
    return _seed_automation_task(gql_context)


@pytest.fixture(scope="module")
def source_solution_ids(gql_context, rgt_id):
    """Two upstream InversionSolutions to aggregate."""
    id1 = _seed_inversion_solution(gql_context, rgt_id, "upstream_a.zip")
    id2 = _seed_inversion_solution(gql_context, rgt_id, "upstream_b.zip")
    return [id1, id2]


@pytest.fixture(scope="module")
def common_rupture_set_id(gql_context):
    return _seed_rupture_set(gql_context, "common_rupture_set.zip")


@pytest.fixture(scope="module")
def created_aggregate(gql_context, automation_task_id, source_solution_ids, common_rupture_set_id):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "aggregate_v1.zip",
                "source_solutions": source_solution_ids,
                "common_rupture_set": common_rupture_set_id,
                "aggregation_fn": "MEAN",
                "produced_by": automation_task_id,
                "md5_digest": "deadbeef",
                "file_size": 4096,
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_aggregate_inversion_solution"]["solution"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_returns_id(created_aggregate):
    gid = created_aggregate["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("AggregateInversionSolution:"), decoded


def test_fields(created_aggregate):
    s = created_aggregate
    assert s["file_name"] == "aggregate_v1.zip"
    assert s["md5_digest"] == "deadbeef"
    assert s["file_size"] == 4096
    assert s["created"] == "2024-05-01T00:00:00Z"
    assert s["aggregation_fn"] == "MEAN"


def test_source_solutions(created_aggregate, source_solution_ids):
    returned_ids = {ss["id"] for ss in created_aggregate["source_solutions"]}
    for sid in source_solution_ids:
        assert sid in returned_ids, f"{sid} not in source_solutions"


def test_common_rupture_set(created_aggregate, common_rupture_set_id):
    crs = created_aggregate["common_rupture_set"]
    assert crs is not None
    assert crs["id"] == common_rupture_set_id


def test_produced_by(created_aggregate, automation_task_id):
    pb = created_aggregate["produced_by"]
    assert pb is not None
    assert pb["id"] == automation_task_id


def test_node_lookup(created_aggregate, gql_context, automation_task_id, source_solution_ids, common_rupture_set_id):
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": created_aggregate["id"]}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["file_name"] == "aggregate_v1.zip"
    assert node["aggregation_fn"] == "MEAN"
    assert node["produced_by"]["id"] == automation_task_id
    assert node["common_rupture_set"]["id"] == common_rupture_set_id
    returned_ids = {ss["id"] for ss in node["source_solutions"]}
    for sid in source_solution_ids:
        assert sid in returned_ids


def test_with_predecessors(gql_context, automation_task_id, source_solution_ids, common_rupture_set_id):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "aggregate_with_pred.zip",
                "source_solutions": source_solution_ids,
                "common_rupture_set": common_rupture_set_id,
                "aggregation_fn": "MEAN",
                "produced_by": automation_task_id,
                "md5_digest": "cafecafe",
                "file_size": 2048,
                "created": "2024-05-02T00:00:00Z",
                "predecessors": [{"id": source_solution_ids[0], "depth": -1}],
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    preds = result.data["create_aggregate_inversion_solution"]["solution"]["predecessors"]
    assert len(preds) == 1
    assert preds[0]["id"] == source_solution_ids[0]
    assert preds[0]["relationship"] == "Parent"
