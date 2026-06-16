"""Ported from graphql_api/tests/hazard/test_bugfix_167_missing_fileunion.py.

Bug #167: AutomationTask.files traversal `... on FileInterface { file_name }`
must resolve when the file is an AggregateInversionSolution. Original bug:
FileUnion didn't include AggregateInversionSolution, so the link couldn't be
resolved.

POC's FileUnion already includes AggregateInversionSolution; this test
verifies the integration works end-to-end.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_AT_AGGREGATE = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    task_type: AGGREGATE_SOLUTION
    model_type: CRUSTAL
    created: $created
    duration: 1
  }) { task_result { id } }
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

CREATE_INVERSION = """
mutation ($input: CreateInversionSolutionInput!) {
  create_inversion_solution(input: $input) { inversion_solution { id } }
}
"""

CREATE_FILE = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size) {
    file_result { id }
  }
}
"""

CREATE_AGGREGATE = """
mutation ($input: CreateAggregateInversionSolutionInput!) {
  create_aggregate_inversion_solution(input: $input) {
    solution { id file_name }
  }
}
"""

CREATE_FILE_RELATION = """
mutation ($thing_id: ID!, $file_id: ID!, $role: FileRole!) {
  create_file_relation(thing_id: $thing_id, file_id: $file_id, role: $role) { ok }
}
"""

QUERY_AT_FILES = """
query ($id: ID!) {
  node(id: $id) {
    ... on AutomationTask {
      id
      model_type
      files {
        total_count
        edges {
          node {
            role
            file {
              __typename
              ... on Node { id }
              ... on FileInterface { file_name }
            }
          }
        }
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def scenario(gql_context):
    created = dt.datetime.now(tzutc()).isoformat()

    rgt = schema.execute_sync(CREATE_RGT, variable_values={"created": created}, context_value=gql_context)
    assert rgt.errors is None, rgt.errors
    rgt_id = rgt.data["create_rupture_generation_task"]["task_result"]["id"]

    at = schema.execute_sync(CREATE_AT_AGGREGATE, variable_values={"created": created}, context_value=gql_context)
    assert at.errors is None, at.errors
    at_id = at.data["create_automation_task"]["task_result"]["id"]

    common_ruptset = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "common_ruptset.zip", "md5": "ccrr", "size": 1000},
        context_value=gql_context,
    )
    assert common_ruptset.errors is None, common_ruptset.errors
    common_ruptset_id = common_ruptset.data["create_file"]["file_result"]["id"]

    upstream = schema.execute_sync(
        CREATE_INVERSION,
        variable_values={
            "input": {
                "file_name": "upstream.zip",
                "produced_by": rgt_id,
                "md5_digest": "aabb",
                "file_size": 1024,
                "created": created,
            }
        },
        context_value=gql_context,
    )
    assert upstream.errors is None, upstream.errors
    upstream_id = upstream.data["create_inversion_solution"]["inversion_solution"]["id"]

    agg = schema.execute_sync(
        CREATE_AGGREGATE,
        variable_values={
            "input": {
                "file_name": "agg.zip",
                "produced_by": at_id,
                "source_solutions": [upstream_id],
                "common_rupture_set": common_ruptset_id,
                "aggregation_fn": "MEAN",
                "md5_digest": "ccdd",
                "file_size": 2048,
                "created": created,
            }
        },
        context_value=gql_context,
    )
    assert agg.errors is None, agg.errors
    agg_id = agg.data["create_aggregate_inversion_solution"]["solution"]["id"]

    rel = schema.execute_sync(
        CREATE_FILE_RELATION,
        variable_values={"thing_id": at_id, "file_id": agg_id, "role": "WRITE"},
        context_value=gql_context,
    )
    assert rel.errors is None, rel.errors

    return {"at_id": at_id, "agg_id": agg_id}


def test_files_resolves_aggregate_inversion_solution(scenario, gql_context):
    """The FileUnion must dispatch to AggregateInversionSolution typename."""
    res = schema.execute_sync(QUERY_AT_FILES, variable_values={"id": scenario["at_id"]}, context_value=gql_context)
    assert res.errors is None, res.errors
    node = res.data["node"]
    assert node["files"]["total_count"] == 1
    edge = node["files"]["edges"][0]["node"]
    assert edge["role"] == "WRITE"
    assert edge["file"]["__typename"] == "AggregateInversionSolution"
    assert edge["file"]["id"] == scenario["agg_id"]
    assert edge["file"]["file_name"] == "agg.zip"
