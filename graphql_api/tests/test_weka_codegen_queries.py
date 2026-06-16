"""Ported from graphql_api/tests/test_dynamo_and_s3_queries.py.

Exercises the GeneralTaskChildrenTab query in the exact shape weka's
Relay codegen produces — including `__isNode: __typename` aliases and
multi-inline-fragment type narrowing. This is the canonical weka query
pattern; if it fails, weka's GeneralTask page is broken.

POC tests typically write idiomatic GraphQL; this port keeps the
codegen-emitted shape verbatim so silent breakages in alias / fragment
handling surface.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_GT = """
mutation ($created: DateTime!, $title: String!) {
  create_general_task(input: {
    created: $created
    title: $title
    description: "weka-codegen"
    agent_name: "tester"
    model_type: CRUSTAL
    argument_lists: [{ k: "alpha", v: ["A", "B"] }]
  }) { general_task { id } }
}
"""

CREATE_AT = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    task_type: INVERSION
    created: $created
    duration: 600
    arguments: [{ k: "max_jump_distance", v: "55.5" }]
  }) { task_result { id } }
}
"""

CREATE_TASK_RELATION = """
mutation ($parent_id: ID!, $child_id: ID!) {
  create_task_relation(parent_id: $parent_id, child_id: $child_id) { ok }
}
"""

# Exact shape weka's Relay codegen emits for GeneralTaskChildrenTabQuery.
# `__isNode: __typename` and inline-fragment type narrowing are the
# distinguishing features.
GENERAL_TASK_CHILDREN_TAB_QUERY = """
query GeneralTaskChildrenTabQuery($id: ID!) {
  node(id: $id) {
    __typename
    ... on GeneralTask {
      id
      model_type
      children {
        total_count
        edges {
          node {
            child {
              __typename
              ... on AutomationTask {
                __typename
                id
                created
                duration
                state
                result
                arguments { k v }
              }
              ... on RuptureGenerationTask {
                __typename
                id
                created
                duration
                state
                result
                arguments { k v }
              }
              ... on Node {
                __isNode: __typename
                id
              }
            }
          }
        }
      }
    }
    id
  }
}
"""

# Smaller weka-shape query just to confirm `swept_arguments` + `children { total_count }`
GENERAL_TASK_QUERY = """
query GeneralTaskQuery($id: ID!) {
  node(id: $id) {
    __typename
    ... on GeneralTask {
      id
      title
      description
      notes
      created
      updated
      agent_name
      model_type
      subtask_type
      subtask_count
      subtask_result
      argument_lists { k v }
      swept_arguments
      children { total_count }
    }
    id
  }
}
"""


@pytest.fixture(scope="module")
def chain(gql_context):
    """Build:  GT  →  AT-1
              \\─→ AT-2
    Linked via create_task_relation.
    """
    created = dt.datetime.now(tzutc()).isoformat()

    gt = schema.execute_sync(
        CREATE_GT, variable_values={"created": created, "title": "weka-style"}, context_value=gql_context
    )
    assert gt.errors is None, gt.errors
    gt_id = gt.data["create_general_task"]["general_task"]["id"]

    child_ids = []
    for _ in range(2):
        at = schema.execute_sync(CREATE_AT, variable_values={"created": created}, context_value=gql_context)
        assert at.errors is None, at.errors
        at_id = at.data["create_automation_task"]["task_result"]["id"]
        child_ids.append(at_id)

        rel = schema.execute_sync(
            CREATE_TASK_RELATION,
            variable_values={"parent_id": gt_id, "child_id": at_id},
            context_value=gql_context,
        )
        assert rel.errors is None, rel.errors
        assert rel.data["create_task_relation"]["ok"]

    return {"gt_id": gt_id, "child_ids": child_ids}


def test_general_task_children_tab_query_runs(chain, gql_context):
    """The full weka-shape query must execute without errors."""
    res = schema.execute_sync(
        GENERAL_TASK_CHILDREN_TAB_QUERY,
        variable_values={"id": chain["gt_id"]},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    assert res.data["node"]["__typename"] == "GeneralTask"


def test_general_task_children_total_count(chain, gql_context):
    """children.total_count reflects the seeded task relations."""
    res = schema.execute_sync(
        GENERAL_TASK_CHILDREN_TAB_QUERY,
        variable_values={"id": chain["gt_id"]},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    assert res.data["node"]["children"]["total_count"] == 2


def test_general_task_children_inline_fragments_resolve(chain, gql_context):
    """Each child resolves with its concrete __typename + arguments."""
    res = schema.execute_sync(
        GENERAL_TASK_CHILDREN_TAB_QUERY,
        variable_values={"id": chain["gt_id"]},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    edges = res.data["node"]["children"]["edges"]
    assert len(edges) == 2
    for edge in edges:
        child = edge["node"]["child"]
        assert child["__typename"] == "AutomationTask"
        # AutomationTask fragment fields land on the response
        assert child["id"] in chain["child_ids"]
        assert child["state"] == "UNDEFINED"
        # The `__isNode: __typename` alias on the Node fragment shows up
        # alongside __typename — both should populate.
        assert child["__isNode"] == "AutomationTask"


def test_general_task_query_swept_arguments_and_children_count(chain, gql_context):
    """GeneralTaskQuery: swept_arguments + children.total_count both populate."""
    res = schema.execute_sync(
        GENERAL_TASK_QUERY,
        variable_values={"id": chain["gt_id"]},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    gt = res.data["node"]
    assert gt["swept_arguments"] == ["alpha"]
    assert gt["children"]["total_count"] == 2
    assert gt["model_type"] == "CRUSTAL"
