"""Ported from graphql_api/tests/hazard/test_inversion_solution.py.

Exercises legacy Predecessor surface area:
  - `Predecessor.relationship` returns Title Case ("Parent", not "parent")
  - `Predecessor.node { ... on FileInterface { file_name meta } }` resolves
    the predecessor's underlying file
  - Via `PredecessorsInterface` fragment
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema


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

CREATE_FILE = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!, $meta: [KeyValuePairInput]) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size, meta: $meta) {
    file_result { id }
  }
}
"""

CREATE_INVERSION_WITH_PREDECESSORS = """
mutation (
  $file_name: String!,
  $md5: String!,
  $size: BigInt!,
  $produced_by: ID!,
  $created: DateTime!,
  $predecessors: [PredecessorInput]
) {
  create_inversion_solution(input: {
    file_name: $file_name
    md5_digest: $md5
    file_size: $size
    produced_by: $produced_by
    created: $created
    predecessors: $predecessors
  }) {
    inversion_solution {
      id
      predecessors {
        id
        typename
        depth
        relationship
        node {
          ... on FileInterface { file_name meta { k v } }
        }
      }
    }
  }
}
"""

NODE_QUERY = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on PredecessorsInterface {
      predecessors {
        id
        typename
        depth
        relationship
        node {
          __typename
          ... on FileInterface { file_name }
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

    ruptset = schema.execute_sync(
        CREATE_FILE,
        variable_values={
            "file_name": "myruptset.zip",
            "md5": "rsrs",
            "size": 5000,
            "meta": [{"k": "label", "v": "rupset"}],
        },
        context_value=gql_context,
    )
    assert ruptset.errors is None, ruptset.errors
    ruptset_id = ruptset.data["create_file"]["file_result"]["id"]

    inv = schema.execute_sync(
        CREATE_INVERSION_WITH_PREDECESSORS,
        variable_values={
            "file_name": "MyInversion.zip",
            "md5": "iiii",
            "size": 1000,
            "produced_by": rgt_id,
            "created": created,
            "predecessors": [{"id": ruptset_id, "depth": -1}],
        },
        context_value=gql_context,
    )
    assert inv.errors is None, inv.errors
    inv_data = inv.data["create_inversion_solution"]["inversion_solution"]

    return {"inv_id": inv_data["id"], "ruptset_id": ruptset_id, "inv_data": inv_data}


def test_predecessor_relationship_is_title_case_on_create(scenario):
    """relationship `Parent` (capitalized), not `parent`."""
    pred = scenario["inv_data"]["predecessors"][0]
    assert pred["depth"] == -1
    assert pred["relationship"] == "Parent"


def test_predecessor_node_resolves_to_underlying_file_on_create(scenario):
    """Predecessor.node { ... on FileInterface { file_name } } resolves."""
    pred = scenario["inv_data"]["predecessors"][0]
    assert pred["node"] is not None
    assert pred["node"]["file_name"] == "myruptset.zip"


def test_predecessor_node_meta_round_trips(scenario):
    """The resolved node carries the underlying file's meta."""
    pred = scenario["inv_data"]["predecessors"][0]
    meta = {m["k"]: m["v"] for m in pred["node"]["meta"]}
    assert meta["label"] == "rupset"


def test_predecessors_interface_node_lookup(scenario, gql_context):
    """Same shape via `... on PredecessorsInterface` fragment on node(id:)."""
    res = schema.execute_sync(
        NODE_QUERY, variable_values={"id": scenario["inv_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    preds = res.data["node"]["predecessors"]
    assert len(preds) == 1
    p = preds[0]
    assert p["depth"] == -1
    assert p["relationship"] == "Parent"
    assert p["node"]["__typename"] == "File"
    assert p["node"]["file_name"] == "myruptset.zip"
