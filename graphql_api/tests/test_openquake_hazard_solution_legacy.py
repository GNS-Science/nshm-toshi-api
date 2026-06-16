"""Ported from graphql_api/tests/hazard/test_openquake_hazard_solution.py.

Exercises gaps the existing POC test_openquake.py doesn't:
  - OpenquakeHazardSolution.predecessors with depth=-2 returns
    relationship="Grandparent" (fix #7b in action)
  - Required `task_type` on CreateOpenquakeHazardSolutionInput
  - `Predecessor.node` resolves the underlying file (#7a)
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_FILE = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size) {
    file_result { id }
  }
}
"""

CREATE_INVERSION = """
mutation ($input: CreateInversionSolutionInput!) {
  create_inversion_solution(input: $input) { inversion_solution { id } }
}
"""

CREATE_RGT = """
mutation ($created: DateTime!) {
  create_rupture_generation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    task_type: RUPTURE_SET
    created: $created
    duration: 1
  }) { task_result { id } }
}
"""

CREATE_NRML = """
mutation ($input: CreateInversionSolutionNrmlInput!) {
  create_inversion_solution_nrml(input: $input) {
    inversion_solution_nrml { id }
  }
}
"""

CREATE_OQ_TASK = """
mutation ($input: CreateOpenquakeHazardTaskInput!) {
  create_openquake_hazard_task(input: $input) {
    openquake_hazard_task { id }
  }
}
"""

CREATE_OQ_SOLUTION_WITH_TYPE = """
mutation (
  $created: DateTime!,
  $csv_archive_id: ID!,
  $produced_by: ID!,
  $predecessors: [PredecessorInput],
  $task_args_id: ID!
) {
  create_openquake_hazard_solution(input: {
    created: $created
    csv_archive: $csv_archive_id
    produced_by: $produced_by
    predecessors: $predecessors
    task_args: $task_args_id
    task_type: HAZARD
  }) {
    openquake_hazard_solution {
      id
      task_args { id file_name }
      csv_archive { id file_name }
      produced_by { ... on Node { id } }
      predecessors {
        id
        typename
        depth
        relationship
        node {
          ... on FileInterface {
            file_name
          }
        }
      }
    }
  }
}
"""

CREATE_OQ_SOLUTION_NO_TYPE = """
mutation (
  $created: DateTime!,
  $csv_archive_id: ID!,
  $produced_by: ID!,
) {
  create_openquake_hazard_solution(input: {
    created: $created
    csv_archive: $csv_archive_id
    produced_by: $produced_by
  }) {
    openquake_hazard_solution { id }
  }
}
"""


@pytest.fixture(scope="module")
def chain(gql_context):
    """upstream IS  →  InversionSolutionNrml  →  OQ task  →  OQ solution
    with predecessors at depth=-1 (Parent, the NRML) and depth=-2 (Grandparent, the IS).
    """
    created = dt.datetime.now(tzutc()).isoformat()

    rgt = schema.execute_sync(CREATE_RGT, variable_values={"created": created}, context_value=gql_context)
    assert rgt.errors is None, rgt.errors
    rgt_id = rgt.data["create_rupture_generation_task"]["task_result"]["id"]

    # upstream inversion solution
    upstream = schema.execute_sync(
        CREATE_INVERSION,
        variable_values={
            "input": {
                "file_name": "upstream.zip",
                "produced_by": rgt_id,
                "md5_digest": "aabb",
                "file_size": 1024,
                "created": created,
                "meta": [{"k": "upstream-tag", "v": "yes"}],
            }
        },
        context_value=gql_context,
    )
    assert upstream.errors is None, upstream.errors
    upstream_id = upstream.data["create_inversion_solution"]["inversion_solution"]["id"]

    # nrml on the upstream
    nrml = schema.execute_sync(
        CREATE_NRML,
        variable_values={
            "input": {
                "file_name": "model.nrml",
                "md5_digest": "nrnr",
                "file_size": 4096,
                "created": created,
                "source_solution": upstream_id,
            }
        },
        context_value=gql_context,
    )
    assert nrml.errors is None, nrml.errors
    nrml_id = nrml.data["create_inversion_solution_nrml"]["inversion_solution_nrml"]["id"]

    # archives + task_args + OQ task
    csv = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "results.csv", "md5": "csv1", "size": 100},
        context_value=gql_context,
    )
    assert csv.errors is None, csv.errors
    csv_id = csv.data["create_file"]["file_result"]["id"]

    task_args = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "task_args.zip", "md5": "ta01", "size": 200},
        context_value=gql_context,
    )
    assert task_args.errors is None, task_args.errors
    task_args_id = task_args.data["create_file"]["file_result"]["id"]

    oq_task = schema.execute_sync(
        CREATE_OQ_TASK,
        variable_values={
            "input": {
                "state": "UNDEFINED",
                "result": "UNDEFINED",
                "task_type": "HAZARD",
                "created": created,
                "duration": 60,
            }
        },
        context_value=gql_context,
    )
    assert oq_task.errors is None, oq_task.errors
    oq_task_id = oq_task.data["create_openquake_hazard_task"]["openquake_hazard_task"]["id"]

    return {
        "upstream_id": upstream_id,
        "nrml_id": nrml_id,
        "csv_id": csv_id,
        "task_args_id": task_args_id,
        "oq_task_id": oq_task_id,
        "created": created,
    }


def test_create_oq_solution_requires_task_type(chain, gql_context):
    """Omitting task_type yields a GraphQL validation error mentioning the field."""
    res = schema.execute_sync(
        CREATE_OQ_SOLUTION_NO_TYPE,
        variable_values={
            "created": chain["created"],
            "csv_archive_id": chain["csv_id"],
            "produced_by": chain["oq_task_id"],
        },
        context_value=gql_context,
    )
    assert res.errors is not None
    text = " ".join(str(e) for e in res.errors).lower()
    assert "task_type" in text, f"missing task_type error didn't mention the field: {res.errors}"


def test_create_oq_solution_with_grandparent_and_parent_predecessors(chain, gql_context):
    """Depth -1 → 'Parent', depth -2 → 'Grandparent'. Both resolve via node."""
    res = schema.execute_sync(
        CREATE_OQ_SOLUTION_WITH_TYPE,
        variable_values={
            "created": chain["created"],
            "csv_archive_id": chain["csv_id"],
            "produced_by": chain["oq_task_id"],
            "predecessors": [
                {"id": chain["upstream_id"], "depth": -2},
                {"id": chain["nrml_id"], "depth": -1},
            ],
            "task_args_id": chain["task_args_id"],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    sol = res.data["create_openquake_hazard_solution"]["openquake_hazard_solution"]
    preds = sol["predecessors"]
    by_depth = {p["depth"]: p for p in preds}

    grand = by_depth[-2]
    assert grand["relationship"] == "Grandparent"
    assert grand["node"]["file_name"] == "upstream.zip"

    parent = by_depth[-1]
    assert parent["relationship"] == "Parent"
    assert parent["node"]["file_name"] == "model.nrml"


def test_oq_solution_csv_and_task_args_resolve(chain, gql_context):
    """csv_archive and task_args resolvers return the right file_name."""
    res = schema.execute_sync(
        CREATE_OQ_SOLUTION_WITH_TYPE,
        variable_values={
            "created": chain["created"],
            "csv_archive_id": chain["csv_id"],
            "produced_by": chain["oq_task_id"],
            "predecessors": [],
            "task_args_id": chain["task_args_id"],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    sol = res.data["create_openquake_hazard_solution"]["openquake_hazard_solution"]
    assert sol["csv_archive"]["file_name"] == "results.csv"
    assert sol["task_args"]["file_name"] == "task_args.zip"
