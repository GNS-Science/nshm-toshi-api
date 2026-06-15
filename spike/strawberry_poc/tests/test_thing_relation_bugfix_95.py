"""Ported from graphql_api/tests/test_thing_relation_bugfix_95.py.

Original test exercised three things that #322 touches:
  1. `create_task_relation` is positional, not input-wrapped
  2. `arguments`/`environment` are list-of-nullable-KeyValuePair inputs
  3. AutomationTask exposes a `parents { edges { node { parent { ... } } } }`
     connection that resolves back to the parent GeneralTask

Legacy test mocked the data layer; this port seeds via real GraphQL
mutations against the testcontainers-backed DynamoDB, then queries.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from schema import schema


CREATE_GT = """
mutation new_gt ($created: DateTime!) {
  create_general_task(input:{
    created: $created
    title: "TEST Build opensha rupture set Coulomb #1"
    description: "Using "
    agent_name: "chrisbc"
  })
  {
    general_task { id }
  }
}
"""

CREATE_AUTOMATION_TASK = """
mutation ($created: DateTime!) {
    create_automation_task(input: {
        state: UNDEFINED
        result: UNDEFINED
        created: $created
        duration: 600
        task_type: RUPTURE_SET

        arguments: [
            { k:"max_jump_distance" v: "55.5" }
            { k:"max_sub_section_length" v: "2" }
            { k:"max_cumulative_azimuth" v: "590" }
            { k:"min_sub_sections_per_parent" v: "2" }
            { k:"permutation_strategy" v: "DOWNDIP" }
        ]

        environment: [
            { k:"gitref_opensha_ucerf3" v: "ABC"}
            { k:"gitref_opensha_commons" v: "ABC"}
            { k:"gitref_opensha_core" v: "ABC"}
            { k:"nshm_nz_opensha" v: "ABC"}
            { k:"host" v:"tryharder-ubuntu"}
            { k:"JAVA" v:"-Xmx24G"  }
        ]
    })
    {
        task_result {
            id
            created
            duration
            arguments { k v }
        }
    }
}
"""

CREATE_GT_RELATION = """
mutation new_gt_link ($parent_id: ID!, $child_id: ID!) {
  create_task_relation(
    parent_id: $parent_id
    child_id: $child_id
  )
  {
    ok
    thing_relation { child_id }
  }
}
"""

QUERY_AT_PARENT = """
query get_task ($id: ID!) {
  node(id: $id) {
    __typename
    ... on AutomationTask {
      id
      created
      duration
      state
      result
      parents {
        edges {
          node {
            parent {
              ... on GeneralTask {
                id
                title
                description
              }
            }
          }
        }
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def seeded(gql_context):
    created = dt.datetime.now(tzutc()).isoformat()

    gt_res = schema.execute_sync(
        CREATE_GT, variable_values={"created": created}, context_value=gql_context
    )
    assert gt_res.errors is None, gt_res.errors
    gt_id = gt_res.data["create_general_task"]["general_task"]["id"]

    at_res = schema.execute_sync(
        CREATE_AUTOMATION_TASK, variable_values={"created": created}, context_value=gql_context
    )
    assert at_res.errors is None, at_res.errors
    at_id = at_res.data["create_automation_task"]["task_result"]["id"]

    rel_res = schema.execute_sync(
        CREATE_GT_RELATION,
        variable_values={"parent_id": gt_id, "child_id": at_id},
        context_value=gql_context,
    )
    assert rel_res.errors is None, rel_res.errors
    assert rel_res.data["create_task_relation"]["ok"] is True

    return {"gt_id": gt_id, "at_id": at_id}


def test_create_general_task_returns_id(seeded):
    """GT mutation returned a relay-encoded id."""
    assert seeded["gt_id"].startswith("R2VuZXJhbFRhc2s6")  # base64("GeneralTask:")


def test_create_automation_task_returns_id(seeded):
    """AT mutation returned a relay-encoded id."""
    assert seeded["at_id"].startswith("QXV0b21hdGlvblRhc2s6")  # base64("AutomationTask:")


def test_at_parents_connection_resolves_general_task(seeded, gql_context):
    """The #322-renamed Connection field `parents { edges { node { parent } } }`
    on AutomationTask resolves back to the seeded GeneralTask.
    """
    res = schema.execute_sync(
        QUERY_AT_PARENT, variable_values={"id": seeded["at_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    node = res.data["node"]
    assert node["__typename"] == "AutomationTask"
    assert node["id"] == seeded["at_id"]
    edges = node["parents"]["edges"]
    assert len(edges) == 1
    parent = edges[0]["node"]["parent"]
    assert parent["id"] == seeded["gt_id"]
    assert parent["title"] == "TEST Build opensha rupture set Coulomb #1"


def test_at_arguments_input_list_nullability(seeded, gql_context):
    """The arguments list field accepts the legacy [KeyValuePairInput] shape.
    Verifies #322's `list[KeyValuePairInput | None]` SDL emission.
    """
    res = schema.execute_sync(
        QUERY_AT_PARENT, variable_values={"id": seeded["at_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    # Argument list itself isn't reselected in this query; assert via a fresh node lookup.
    Q = """
    query ($id: ID!) {
      node(id: $id) {
        ... on AutomationTask {
          arguments { k v }
        }
      }
    }
    """
    arg_res = schema.execute_sync(Q, variable_values={"id": seeded["at_id"]}, context_value=gql_context)
    assert arg_res.errors is None, arg_res.errors
    args = {a["k"]: a["v"] for a in arg_res.data["node"]["arguments"]}
    assert args["max_jump_distance"] == "55.5"
    assert args["permutation_strategy"] == "DOWNDIP"
