"""Ported from graphql_api/tests/test_source_solution_bugfix_214.py.

Bug #214: ScaledInversionSolution.source_solution returned the wrong
__typename when the upstream was a TimeDependentInversionSolution.
The dispatch must select the concrete subtype, not a generic node.

POC's existing test_scaled_inversion_solution.py tests source_solution
only with InversionSolution as the source. This file fills the gap.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from schema import schema


CREATE_AT = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    created: $created
    duration: 1
    task_type: INVERSION
  }) { task_result { id } }
}
"""

CREATE_INVERSION = """
mutation ($input: CreateInversionSolutionInput!) {
  create_inversion_solution(input: $input) { inversion_solution { id } }
}
"""

CREATE_TIME_DEPENDENT = """
mutation ($input: CreateTimeDependentInversionSolutionInput!) {
  create_time_dependent_inversion_solution(input: $input) {
    solution { id }
  }
}
"""

CREATE_SCALED = """
mutation ($input: CreateScaledInversionSolutionInput!) {
  create_scaled_inversion_solution(input: $input) {
    solution {
      id
      source_solution {
        __typename
        ... on Node { id }
      }
    }
  }
}
"""

QUERY_SCALED_NODE = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on ScaledInversionSolution {
      id
      source_solution {
        __typename
        ... on Node { id }
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def chain(gql_context):
    """Build:  inv (upstream)  ←  time_dep  ←  scaled

    Such that:
      time_dep.source_solution = inv
      scaled.source_solution   = time_dep
    """
    created = dt.datetime.now(tzutc()).isoformat()

    at_res = schema.execute_sync(CREATE_AT, variable_values={"created": created}, context_value=gql_context)
    assert at_res.errors is None, at_res.errors
    at_id = at_res.data["create_automation_task"]["task_result"]["id"]

    inv_res = schema.execute_sync(
        CREATE_INVERSION,
        variable_values={
            "input": {
                "file_name": "upstream.zip",
                "produced_by": at_id,
                "md5_digest": "aabb",
                "file_size": 1024,
                "created": created,
            }
        },
        context_value=gql_context,
    )
    assert inv_res.errors is None, inv_res.errors
    inv_id = inv_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    td_res = schema.execute_sync(
        CREATE_TIME_DEPENDENT,
        variable_values={
            "input": {
                "file_name": "td_v1.zip",
                "produced_by": at_id,
                "source_solution": inv_id,
                "md5_digest": "ccdd",
                "file_size": 2048,
                "created": created,
            }
        },
        context_value=gql_context,
    )
    assert td_res.errors is None, td_res.errors
    td_id = td_res.data["create_time_dependent_inversion_solution"]["solution"]["id"]

    scaled_res = schema.execute_sync(
        CREATE_SCALED,
        variable_values={
            "input": {
                "file_name": "scaled_v1.zip",
                "produced_by": at_id,
                "source_solution": td_id,
                "md5_digest": "eeff",
                "file_size": 512,
                "created": created,
            }
        },
        context_value=gql_context,
    )
    assert scaled_res.errors is None, scaled_res.errors
    scaled_data = scaled_res.data["create_scaled_inversion_solution"]["solution"]

    return {"inv_id": inv_id, "td_id": td_id, "scaled_id": scaled_data["id"], "scaled_data": scaled_data}


def test_scaled_source_solution_dispatches_to_time_dependent_on_create(chain):
    """Bug #214: the mutation response's source_solution.__typename must be
    'TimeDependentInversionSolution', not a generic node or InversionSolution.
    """
    ss = chain["scaled_data"]["source_solution"]
    assert ss is not None
    assert ss["__typename"] == "TimeDependentInversionSolution"
    assert ss["id"] == chain["td_id"]


def test_scaled_source_solution_dispatches_to_time_dependent_via_node_lookup(chain, gql_context):
    """Same assertion via a node lookup — separate code path (resolve_node)."""
    res = schema.execute_sync(
        QUERY_SCALED_NODE, variable_values={"id": chain["scaled_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    ss = res.data["node"]["source_solution"]
    assert ss["__typename"] == "TimeDependentInversionSolution"
    assert ss["id"] == chain["td_id"]
