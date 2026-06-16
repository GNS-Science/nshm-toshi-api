"""Ported from graphql_api/tests/hazard/test_file.py.

Bug #10 (caught by porting): plain File needs `predecessors` parity with
legacy. Legacy SDL:
  - CreateFile accepts `predecessors: [PredecessorInput]`
  - File implements PredecessorsInterface (selectable as
    `... on PredecessorsInterface { predecessors { ... } }`)

POC originally omitted both with a comment that no client used them.
The legacy test shows that File-with-predecessors is a real shape —
clients chaining files via predecessor edges need it to work.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema


CREATE_FILE_NO_PRED = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size) {
    file_result { id }
  }
}
"""

CREATE_FILE_WITH_PRED = """
mutation (
  $file_name: String!,
  $md5: String!,
  $size: BigInt!,
  $predecessors: [PredecessorInput],
) {
  create_file(
    file_name: $file_name,
    md5_digest: $md5,
    file_size: $size,
    predecessors: $predecessors,
  ) {
    file_result {
      id
      file_name
      predecessors {
        id
        depth
        relationship
        typename
      }
    }
  }
}
"""

QUERY_FILE_PREDECESSORS_VIA_INTERFACE = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on FileInterface { file_name }
    ... on PredecessorsInterface {
      predecessors {
        id
        depth
        relationship
        typename
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
def upstream_file_id(gql_context):
    res = schema.execute_sync(
        CREATE_FILE_NO_PRED,
        variable_values={"file_name": "source_solution.zip", "md5": "ssss", "size": 1000},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_file"]["file_result"]["id"]


def test_create_file_with_predecessors_returns_chain(upstream_file_id, gql_context):
    """Legacy regression: create_file accepts predecessors and returns them."""
    res = schema.execute_sync(
        CREATE_FILE_WITH_PRED,
        variable_values={
            "file_name": "downstream.zip",
            "md5": "dddd",
            "size": 2000,
            "predecessors": [{"id": upstream_file_id, "depth": -1}],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    result = res.data["create_file"]["file_result"]
    preds = result["predecessors"]
    assert len(preds) == 1
    assert preds[0]["id"] == upstream_file_id
    assert preds[0]["depth"] == -1
    assert preds[0]["relationship"] == "Parent"
    assert preds[0]["typename"] == "File"


def test_file_via_predecessors_interface(upstream_file_id, gql_context):
    """File must be selectable via `... on PredecessorsInterface`."""
    create = schema.execute_sync(
        CREATE_FILE_WITH_PRED,
        variable_values={
            "file_name": "downstream2.zip",
            "md5": "dd22",
            "size": 2048,
            "predecessors": [{"id": upstream_file_id, "depth": -1}],
        },
        context_value=gql_context,
    )
    assert create.errors is None, create.errors
    downstream_id = create.data["create_file"]["file_result"]["id"]

    res = schema.execute_sync(
        QUERY_FILE_PREDECESSORS_VIA_INTERFACE,
        variable_values={"id": downstream_id},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    node = res.data["node"]
    assert node["__typename"] == "File"
    assert node["file_name"] == "downstream2.zip"
    preds = node["predecessors"]
    assert len(preds) == 1
    assert preds[0]["relationship"] == "Parent"
    # The resolved Predecessor.node points back at the upstream File
    assert preds[0]["node"]["__typename"] == "File"
    assert preds[0]["node"]["file_name"] == "source_solution.zip"


def test_file_without_predecessors_returns_null(gql_context):
    """A File created without predecessors returns null/empty when queried."""
    create = schema.execute_sync(
        CREATE_FILE_NO_PRED,
        variable_values={"file_name": "no_predecessors.zip", "md5": "nnnn", "size": 512},
        context_value=gql_context,
    )
    assert create.errors is None, create.errors
    file_id = create.data["create_file"]["file_result"]["id"]

    res = schema.execute_sync(
        QUERY_FILE_PREDECESSORS_VIA_INTERFACE,
        variable_values={"id": file_id},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    preds = res.data["node"]["predecessors"]
    # Legacy returns null/None when no predecessors; either an empty list or
    # null is acceptable as long as no GraphQLError surfaces.
    assert preds is None or preds == []
