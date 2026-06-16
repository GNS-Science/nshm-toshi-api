"""
Tests for the `nodes(id_in: [...])` batch-fetch query.

Mirrors legacy test_nodes_bugfix_220.py, which exercises the primary
weka client query pattern: fetch a ScaledInversionSolution by id,
expand its source_solution and produced_by, then traverse produced_by →
parents → GeneralTask in a single round-trip.

Note: legacy schema had an `AutomationTaskInterface`; the POC uses the
concrete `AutomationTask` type. The traversal pattern is otherwise identical.

Covers COVERAGE_GAPS.md gap 3.
"""

import base64

import pytest

from graphql_api.schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

NODES_BASIC_QUERY = """
query NodesBasic($ids: [ID!]!) {
    nodes(id_in: $ids) {
        ok
        result {
            edges {
                node {
                    __typename
                    ... on ScaledInversionSolution { id }
                    ... on InversionSolution { id }
                    ... on AutomationTask { id }
                }
            }
        }
    }
}
"""

NODES_INTERFACE_QUERY = """
query NodesInterface($ids: [ID!]!) {
    nodes(id_in: $ids) {
        result {
            edges {
                node {
                    __typename
                    ... on InversionSolutionInterface {
                        file_name
                        mfd_table_id
                        tables { table_id table_type }
                    }
                }
            }
        }
    }
}
"""

NODES_DEEP_QUERY = """
query NodesDeep($ids: [ID!]!) {
    nodes(id_in: $ids) {
        result {
            edges {
                node {
                    __typename
                    ... on ScaledInversionSolution {
                        id
                        file_name
                        source_solution {
                            __typename
                            ... on InversionSolution { id file_name }
                        }
                        produced_by {
                            __typename
                            ... on AutomationTask {
                                id
                                task_type
                                parents {
                                    edges {
                                        node {
                                            parent {
                                                __typename
                                                ... on GeneralTask { id title }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

CREATE_GT_MUTATION = """
mutation($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) { general_task { id } }
}
"""

CREATE_AT_MUTATION = """
mutation($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) { task_result { id } }
}
"""

CREATE_IS_MUTATION = """
mutation($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) { inversion_solution { id } }
}
"""

CREATE_SIS_MUTATION = """
mutation($input: CreateScaledInversionSolutionInput!) {
    create_scaled_inversion_solution(input: $input) { solution { id } }
}
"""

CREATE_TASK_RELATION_MUTATION = """
mutation($child_id: ID!, $parent_id: ID!) {
    create_task_relation(child_id: $child_id, parent_id: $parent_id) { ok }
}
"""


# ── Seeds ─────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def chain(gql_context):
    """Seed GT → AT (linked as child of GT) → IS (produced by AT) → SIS (produced by AT, source = IS)."""
    gt_result = schema.execute_sync(
        CREATE_GT_MUTATION,
        variable_values={"input": {"title": "weka-pattern parent GT", "agent_name": "pytest"}},
        context_value=gql_context,
    )
    assert gt_result.errors is None, gt_result.errors
    gt_id = gt_result.data["create_general_task"]["general_task"]["id"]

    at_result = schema.execute_sync(
        CREATE_AT_MUTATION,
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
    assert at_result.errors is None, at_result.errors
    at_id = at_result.data["create_automation_task"]["task_result"]["id"]

    rel_result = schema.execute_sync(
        CREATE_TASK_RELATION_MUTATION,
        variable_values={"parent_id": gt_id, "child_id": at_id},
        context_value=gql_context,
    )
    assert rel_result.errors is None, rel_result.errors

    is_result = schema.execute_sync(
        CREATE_IS_MUTATION,
        variable_values={
            "input": {
                "file_name": "weka_pattern.zip",
                "produced_by": at_id,
                "md5_digest": "1111",
                "file_size": 1024,
                "created": "2024-02-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert is_result.errors is None, is_result.errors
    is_id = is_result.data["create_inversion_solution"]["inversion_solution"]["id"]

    sis_result = schema.execute_sync(
        CREATE_SIS_MUTATION,
        variable_values={
            "input": {
                "file_name": "weka_pattern_scaled.zip",
                "source_solution": is_id,
                "produced_by": at_id,
                "md5_digest": "2222",
                "file_size": 2048,
                "created": "2024-02-02T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert sis_result.errors is None, sis_result.errors
    sis_id = sis_result.data["create_scaled_inversion_solution"]["solution"]["id"]

    return {"gt_id": gt_id, "at_id": at_id, "is_id": is_id, "sis_id": sis_id}


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_nodes_basic_returns_typename_and_id(gql_context, chain):
    """nodes(id_in: [mixed]) returns matching __typename and id for each."""
    ids = [chain["sis_id"], chain["is_id"], chain["at_id"]]
    result = schema.execute_sync(NODES_BASIC_QUERY, variable_values={"ids": ids}, context_value=gql_context)
    assert result.errors is None, result.errors
    edges = result.data["nodes"]["result"]["edges"]
    nodes = [e["node"] for e in edges]
    typenames = {n["__typename"] for n in nodes}
    assert typenames == {"ScaledInversionSolution", "InversionSolution", "AutomationTask"}
    returned_ids = {n["id"] for n in nodes}
    assert returned_ids == set(ids)


def test_nodes_with_unknown_id_skips_silently(gql_context, chain):
    """An invalid/unknown global ID should be skipped, not error."""
    fake_id = base64.b64encode(b"NoSuchType:00000nope").decode()
    result = schema.execute_sync(
        NODES_BASIC_QUERY,
        variable_values={"ids": [chain["sis_id"], fake_id]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    edges = result.data["nodes"]["result"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["id"] == chain["sis_id"]


def test_nodes_expand_inversion_solution_interface(gql_context, chain):
    """Expand `... on InversionSolutionInterface` on a ScaledInversionSolution
    via the nodes query — this is the weka fragment pattern."""
    result = schema.execute_sync(
        NODES_INTERFACE_QUERY,
        variable_values={"ids": [chain["sis_id"]]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["nodes"]["result"]["edges"][0]["node"]
    assert node["__typename"] == "ScaledInversionSolution"
    assert node["file_name"] == "weka_pattern_scaled.zip"
    # ScaledIS without tables → mfd_table_id is null
    assert node["mfd_table_id"] is None


def test_nodes_deep_parent_traversal(gql_context, chain):
    """Canonical weka pattern: fetch ScaledIS → expand produced_by AutomationTask
    → traverse parents to retrieve the parent GeneralTask in one request."""
    result = schema.execute_sync(
        NODES_DEEP_QUERY,
        variable_values={"ids": [chain["sis_id"]]},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    node = result.data["nodes"]["result"]["edges"][0]["node"]
    assert node["__typename"] == "ScaledInversionSolution"
    assert node["id"] == chain["sis_id"]
    assert node["source_solution"]["__typename"] == "InversionSolution"
    assert node["source_solution"]["id"] == chain["is_id"]

    produced_by = node["produced_by"]
    assert produced_by["__typename"] == "AutomationTask"
    assert produced_by["id"] == chain["at_id"]
    assert produced_by["task_type"] == "INVERSION"

    parent_edges = produced_by["parents"]["edges"]
    assert len(parent_edges) == 1
    parent = parent_edges[0]["node"]["parent"]
    assert parent["__typename"] == "GeneralTask"
    assert parent["id"] == chain["gt_id"]
    assert parent["title"] == "weka-pattern parent GT"
