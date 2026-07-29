"""Regression: `relations` must be queryable via a `... on FileInterface` fragment.

The legacy Graphene schema declared `relations` on FileInterface itself
(pre-ADR-004 `graphql_api/schema/file.py`); the Strawberry port declared it only
on some concrete types. A client selecting

    ... on FileInterface { relations { total_count } }

therefore failed GraphQL *validation*, which nulls the entire document — every
sibling node came back null, not just `relations`.

Two silent halves of the same bug are covered here too:
  - RuptureSet and InversionSolutionNrml had no `relations` field at all, even
    though their DynamoDB records carry the data.
  - The four InversionSolution types returned a bespoke non-Relay type, so the
    legacy `relations { edges { node { ... } } }` shape failed on them.
"""

import pytest

from graphql_api.schema import schema

# ── Mutations ─────────────────────────────────────────────────────────────────

CREATE_TASK = """
mutation ($input: CreateAutomationTaskInput!) {
    create_rupture_generation_task(input: $input) { task_result { id } }
}
"""

CREATE_FILE = """
mutation ($file_name: String!, $md5_digest: String!, $file_size: BigInt!) {
    create_file(file_name: $file_name, md5_digest: $md5_digest, file_size: $file_size) {
        file_result { id }
    }
}
"""

CREATE_SMS_FILE = """
mutation ($input: CreateSmsFileInput!) {
    create_sms_file(input: $input) { file_result { id } }
}
"""

CREATE_RUPTURE_SET = """
mutation ($input: CreateRuptureSetInput!) {
    create_rupture_set(input: $input) { rupture_set { id } }
}
"""

CREATE_INVERSION_SOLUTION = """
mutation ($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) { inversion_solution { id } }
}
"""

CREATE_SCALED = """
mutation ($input: CreateScaledInversionSolutionInput!) {
    create_scaled_inversion_solution(input: $input) { solution { id } }
}
"""

CREATE_AGGREGATE = """
mutation ($input: CreateAggregateInversionSolutionInput!) {
    create_aggregate_inversion_solution(input: $input) { solution { id } }
}
"""

CREATE_TIME_DEPENDENT = """
mutation ($input: CreateTimeDependentInversionSolutionInput!) {
    create_time_dependent_inversion_solution(input: $input) { solution { id } }
}
"""

CREATE_NRML = """
mutation ($input: CreateInversionSolutionNrmlInput!) {
    create_inversion_solution_nrml(input: $input) { inversion_solution_nrml { id } }
}
"""

CREATE_FILE_RELATION = """
mutation ($file_id: ID!, $role: FileRole!, $thing_id: ID!) {
    create_file_relation(file_id: $file_id, role: $role, thing_id: $thing_id) { ok }
}
"""

# ── Queries ───────────────────────────────────────────────────────────────────

# The exact shape that was failing in the field.
FILE_INTERFACE_FRAGMENT_QUERY = """
query ($id: ID!) {
    node(id: $id) {
        __typename
        ... on FileInterface {
            file_name
            relations { total_count }
        }
    }
}
"""

# Legacy Relay edge shape — broken on the InversionSolution family pre-fix.
RELATIONS_EDGES_QUERY = """
query ($id: ID!) {
    node(id: $id) {
        ... on FileInterface {
            relations {
                total_count
                edges { node { role thing_id } }
            }
        }
    }
}
"""

RUPTURE_SET_ROUNDTRIP_QUERY = """
query ($id: ID!) {
    node(id: $id) {
        ... on RuptureSet {
            relations {
                total_count
                edges {
                    node {
                        role
                        thing { ... on RuptureGenerationTask { id } }
                    }
                }
            }
        }
    }
}
"""


def _run(query, gql_context, **variables):
    result = schema.execute_sync(query, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    return result.data


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def task_id(gql_context):
    """A RuptureGenerationTask to hang every file relation off."""
    data = _run(
        CREATE_TASK,
        gql_context,
        input={
            "state": "UNDEFINED",
            "result": "UNDEFINED",
            "task_type": "RUPTURE_SET",
            "created": "2026-07-29T00:00:00Z",
        },
    )
    return data["create_rupture_generation_task"]["task_result"]["id"]


@pytest.fixture(scope="module")
def file_ids(gql_context, task_id):
    """Create one of every FileInterface implementor, each linked to `task_id`.

    Returns {SDL type name: global id}. Creation order matters: the scaled,
    aggregate and time-dependent solutions reference earlier ones.
    """
    ids: dict[str, str] = {}

    ids["File"] = _run(CREATE_FILE, gql_context, file_name="plain.zip", md5_digest="aaa==", file_size=100)[
        "create_file"
    ]["file_result"]["id"]

    ids["SmsFile"] = _run(CREATE_SMS_FILE, gql_context, input={"file_name": "sms.csv", "file_type": "CPT"})[
        "create_sms_file"
    ]["file_result"]["id"]

    ids["RuptureSet"] = _run(
        CREATE_RUPTURE_SET,
        gql_context,
        input={
            "file_name": "rupture_set.zip",
            "md5_digest": "bbb==",
            "file_size": 200,
            "produced_by": task_id,
        },
    )["create_rupture_set"]["rupture_set"]["id"]

    ids["InversionSolution"] = _run(CREATE_INVERSION_SOLUTION, gql_context, input={"file_name": "solution.zip"})[
        "create_inversion_solution"
    ]["inversion_solution"]["id"]

    ids["ScaledInversionSolution"] = _run(
        CREATE_SCALED,
        gql_context,
        input={"file_name": "scaled.zip", "source_solution": ids["InversionSolution"]},
    )["create_scaled_inversion_solution"]["solution"]["id"]

    ids["AggregateInversionSolution"] = _run(
        CREATE_AGGREGATE,
        gql_context,
        input={
            "file_name": "aggregate.zip",
            "common_rupture_set": ids["RuptureSet"],
            "source_solutions": [ids["InversionSolution"]],
            "aggregation_fn": "MEAN",
        },
    )["create_aggregate_inversion_solution"]["solution"]["id"]

    ids["TimeDependentInversionSolution"] = _run(
        CREATE_TIME_DEPENDENT,
        gql_context,
        input={"file_name": "time_dep.zip", "source_solution": ids["InversionSolution"]},
    )["create_time_dependent_inversion_solution"]["solution"]["id"]

    ids["InversionSolutionNrml"] = _run(CREATE_NRML, gql_context, input={"file_name": "solution.xml"})[
        "create_inversion_solution_nrml"
    ]["inversion_solution_nrml"]["id"]

    for file_id in ids.values():
        _run(CREATE_FILE_RELATION, gql_context, file_id=file_id, role="WRITE", thing_id=task_id)

    return ids


ALL_FILE_TYPES = [
    "File",
    "SmsFile",
    "RuptureSet",
    "InversionSolution",
    "ScaledInversionSolution",
    "AggregateInversionSolution",
    "TimeDependentInversionSolution",
    "InversionSolutionNrml",
]


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("type_name", ALL_FILE_TYPES)
def test_relations_via_file_interface_fragment(gql_context, file_ids, type_name):
    """`... on FileInterface { relations { total_count } }` resolves on every file type.

    Pre-fix this raised "Cannot query field 'relations' on type 'FileInterface'",
    which failed validation and nulled the whole `node` payload.
    """
    data = _run(FILE_INTERFACE_FRAGMENT_QUERY, gql_context, id=file_ids[type_name])

    node = data["node"]
    assert node is not None, f"{type_name}: node came back null"
    assert node["__typename"] == type_name
    # Non-zero: an empty list would pass even if relations_raw were never wired up.
    assert node["relations"]["total_count"] == 1


@pytest.mark.parametrize("type_name", ALL_FILE_TYPES)
def test_relations_uses_legacy_relay_edge_shape(gql_context, file_ids, type_name):
    """`relations { edges { node { ... } } }` is the legacy FileRelationConnection shape.

    The InversionSolution family previously returned a bespoke type whose `edges`
    were bare FileRelation objects with no `node` wrapper, so this selection failed.
    """
    data = _run(RELATIONS_EDGES_QUERY, gql_context, id=file_ids[type_name])

    relations = data["node"]["relations"]
    assert relations["total_count"] == 1
    assert len(relations["edges"]) == 1
    assert relations["edges"][0]["node"]["role"] == "WRITE"


def test_rupture_set_relations_resolve_back_to_task(gql_context, file_ids, task_id):
    """A RuptureSet can report the task it is linked to.

    RuptureSet had no `relations` field at all before this fix, so this link was
    unreachable through the API despite being present in DynamoDB.
    """
    data = _run(RUPTURE_SET_ROUNDTRIP_QUERY, gql_context, id=file_ids["RuptureSet"])

    edges = data["node"]["relations"]["edges"]
    assert len(edges) == 1
    assert edges[0]["node"]["thing"]["id"] == task_id


def test_file_interface_declares_relations_in_sdl():
    """Lock the field onto the interface itself, not just the concrete types."""
    sdl = schema.as_str()
    interface_block = sdl.split("interface FileInterface {")[1].split("\n}")[0]
    assert "): FileRelationConnection!" in interface_block
