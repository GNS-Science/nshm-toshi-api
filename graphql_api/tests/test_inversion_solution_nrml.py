"""
Tests for InversionSolutionNrml — file type with a SourceSolutionUnion source.

Mirrors legacy hazard/test_openquake_sources_nrml_solution.py. Covers
COVERAGE_GAPS.md gap 2 (NRML had zero POC tests previously).
"""

import base64

import pytest

from graphql_api.schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_NRML_MUTATION = """
mutation CreateNrml($input: CreateInversionSolutionNrmlInput!) {
    create_inversion_solution_nrml(input: $input) {
        ok
        inversion_solution_nrml {
            id
            file_name
            md5_digest
            file_size
            created
            source_solution {
                __typename
                ... on InversionSolution { id }
                ... on ScaledInversionSolution { id }
                ... on TimeDependentInversionSolution { id }
            }
            predecessors { id depth relationship typename }
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        __typename
        ... on InversionSolutionNrml {
            file_name
            source_solution {
                __typename
                ... on InversionSolution { id }
                ... on ScaledInversionSolution { id }
                ... on TimeDependentInversionSolution { id }
            }
            predecessors { id depth relationship }
        }
    }
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

CREATE_TDIS_MUTATION = """
mutation($input: CreateTimeDependentInversionSolutionInput!) {
    create_time_dependent_inversion_solution(input: $input) { solution { id } }
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


def _seed_is(gql_context, rgt_id: str) -> str:
    result = schema.execute_sync(
        CREATE_IS_MUTATION,
        variable_values={
            "input": {
                "file_name": "nrml_is.zip",
                "produced_by": rgt_id,
                "md5_digest": "aaaa",
                "file_size": 100,
                "created": "2024-02-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution"]["inversion_solution"]["id"]


def _seed_sis(gql_context, source_is_id: str) -> str:
    result = schema.execute_sync(
        CREATE_SIS_MUTATION,
        variable_values={
            "input": {
                "file_name": "nrml_sis.zip",
                "source_solution": source_is_id,
                "md5_digest": "bbbb",
                "file_size": 200,
                "created": "2024-02-02T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_scaled_inversion_solution"]["solution"]["id"]


def _seed_tdis(gql_context, source_is_id: str) -> str:
    result = schema.execute_sync(
        CREATE_TDIS_MUTATION,
        variable_values={
            "input": {
                "file_name": "nrml_tdis.zip",
                "source_solution": source_is_id,
                "md5_digest": "cccc",
                "file_size": 300,
                "created": "2024-02-03T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_time_dependent_inversion_solution"]["solution"]["id"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    return _seed_rgt(gql_context)


@pytest.fixture(scope="module")
def is_id(gql_context, rgt_id):
    return _seed_is(gql_context, rgt_id)


@pytest.fixture(scope="module")
def sis_id(gql_context, is_id):
    return _seed_sis(gql_context, is_id)


@pytest.fixture(scope="module")
def tdis_id(gql_context, is_id):
    return _seed_tdis(gql_context, is_id)


def _create_nrml(gql_context, source_id: str, file_name: str, predecessors=None):
    payload = {
        "file_name": file_name,
        "source_solution": source_id,
        "md5_digest": "deadbeef",
        "file_size": 2048,
        "created": "2024-03-01T00:00:00Z",
    }
    if predecessors is not None:
        payload["predecessors"] = predecessors
    result = schema.execute_sync(CREATE_NRML_MUTATION, variable_values={"input": payload}, context_value=gql_context)
    assert result.errors is None, result.errors
    return result.data["create_inversion_solution_nrml"]["inversion_solution_nrml"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_nrml_from_inversion_solution(gql_context, is_id):
    nrml = _create_nrml(gql_context, is_id, "nrml_from_is.xml")
    decoded = base64.b64decode(nrml["id"]).decode()
    assert decoded.startswith("InversionSolutionNrml:")
    assert nrml["file_name"] == "nrml_from_is.xml"
    assert nrml["md5_digest"] == "deadbeef"
    assert nrml["file_size"] == 2048
    assert nrml["created"] == "2024-03-01T00:00:00Z"


def test_create_nrml_from_scaled_solution(gql_context, sis_id):
    nrml = _create_nrml(gql_context, sis_id, "nrml_from_sis.xml")
    assert nrml["source_solution"]["__typename"] == "ScaledInversionSolution"
    assert nrml["source_solution"]["id"] == sis_id


def test_create_nrml_from_time_dependent_solution(gql_context, tdis_id):
    nrml = _create_nrml(gql_context, tdis_id, "nrml_from_tdis.xml")
    assert nrml["source_solution"]["__typename"] == "TimeDependentInversionSolution"
    assert nrml["source_solution"]["id"] == tdis_id


def test_source_solution_union_dispatch(gql_context, is_id):
    """source_solution must dispatch to the correct type based on clazz_name."""
    nrml = _create_nrml(gql_context, is_id, "dispatch_check.xml")
    assert nrml["source_solution"]["__typename"] == "InversionSolution"
    assert nrml["source_solution"]["id"] == is_id


def test_nrml_with_predecessors(gql_context, is_id):
    nrml = _create_nrml(
        gql_context,
        is_id,
        "nrml_with_preds.xml",
        predecessors=[{"id": is_id, "depth": -1}],
    )
    preds = nrml["predecessors"]
    assert preds is not None
    assert len(preds) == 1
    assert preds[0]["id"] == is_id
    assert preds[0]["depth"] == -1
    assert preds[0]["relationship"].lower() == "parent"


def test_nrml_node_lookup(gql_context, is_id):
    nrml = _create_nrml(gql_context, is_id, "node_lookup.xml")
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": nrml["id"]}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["__typename"] == "InversionSolutionNrml"
    assert node["file_name"] == "node_lookup.xml"
    assert node["source_solution"]["__typename"] == "InversionSolution"
    assert node["source_solution"]["id"] == is_id
