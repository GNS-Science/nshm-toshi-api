"""Ported from graphql_api/tests/test_general_task_schema.py.

Covers cases the existing POC `test_general_task.py` doesn't:
  - `argument_lists` with `v: [null]` (a single-element list containing null) —
    tests the inner-null path of `list[str | None]` that #322 was supposed to fix
  - `swept_arguments` resolver returning ONLY the keys whose `v` has > 1 element
    (so `v: [null]` should NOT make a key "swept")
  - `meta` round-trip on update mutation
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_GT = """
mutation ($created: DateTime!, $argument_lists: [KeyValueListPairInput], $meta: [KeyValuePairInput]) {
  create_general_task(input: {
    agent_name: "DonDuck"
    title: "host"
    description: "host"
    created: $created
    argument_lists: $argument_lists
    meta: $meta
  })
  {
    general_task {
      id
      argument_lists { k v }
      swept_arguments
      meta { k v }
    }
  }
}
"""

NODE_QUERY_GT = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on GeneralTask {
      id
      argument_lists { k v }
      swept_arguments
      meta { k v }
    }
  }
}
"""

UPDATE_GT = """
mutation ($task_id: ID!, $updated: DateTime!, $meta: [KeyValuePairInput]) {
  update_general_task(input: {
    task_id: $task_id
    updated: $updated
    meta: $meta
  })
  {
    general_task {
      id
      updated
      meta { k v }
      argument_lists { k v }
      swept_arguments
    }
  }
}
"""


@pytest.fixture(scope="module")
def created(gql_context):
    """GT created with mixed argument_lists — one swept ([20,25]), one unswept
    with explicit null element ([null]).
    """
    res = schema.execute_sync(
        CREATE_GT,
        variable_values={
            "created": dt.datetime.now(tzutc()).isoformat(),
            "argument_lists": [
                {"k": "bogus_metric", "v": ["20", "25"]},
                {"k": "unswept_metric", "v": [None]},
            ],
            "meta": [{"k": "some_metric", "v": "55.5"}],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_general_task"]["general_task"]


def test_argument_lists_inner_null_round_trip(created):
    """`v: [null]` survives mutation round-trip — exercises #322's inner-null."""
    al = {item["k"]: item["v"] for item in created["argument_lists"]}
    assert al["bogus_metric"] == ["20", "25"]
    assert al["unswept_metric"] == [None]


def test_swept_arguments_excludes_single_null_list(created):
    """A key with `v: [null]` (one element) is NOT swept — only keys with len(v) > 1."""
    assert created["swept_arguments"] == ["bogus_metric"]


def test_meta_round_trip(created):
    """meta list-of-KeyValuePair round-trips."""
    meta = {item["k"]: item["v"] for item in created["meta"]}
    assert meta["some_metric"] == "55.5"


def test_node_lookup_preserves_argument_lists(created, gql_context):
    """Same shape via node(id:) lookup — separate code path."""
    res = schema.execute_sync(NODE_QUERY_GT, variable_values={"id": created["id"]}, context_value=gql_context)
    assert res.errors is None, res.errors
    node = res.data["node"]
    al = {item["k"]: item["v"] for item in node["argument_lists"]}
    assert al["unswept_metric"] == [None]
    assert node["swept_arguments"] == ["bogus_metric"]


def test_update_with_meta_preserves_argument_lists(created, gql_context):
    """Update modifying only meta must preserve argument_lists / swept_arguments."""
    res = schema.execute_sync(
        UPDATE_GT,
        variable_values={
            "task_id": created["id"],
            "updated": dt.datetime.now(tzutc()).isoformat(),
            "meta": [{"k": "balderdash", "v": "20"}],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    gt = res.data["update_general_task"]["general_task"]
    new_meta = {item["k"]: item["v"] for item in gt["meta"]}
    assert new_meta["balderdash"] == "20"
    # argument_lists must be preserved by the update path
    al = {item["k"]: item["v"] for item in gt["argument_lists"]}
    assert al["bogus_metric"] == ["20", "25"]
    assert al["unswept_metric"] == [None]
    assert gt["swept_arguments"] == ["bogus_metric"]
