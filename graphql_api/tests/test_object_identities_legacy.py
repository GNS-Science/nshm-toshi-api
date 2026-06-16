"""Ported from graphql_api/tests/object_iteration/test_iterate_items.py.

Exercises the `object_identities` query, which has zero POC test coverage
despite being a real wire-facing query that admin / migration tools use.

Schema layer: object_identities(object_type: String!, first: Int, after: String)
returns an ObjectIdentitiesConnection with edges[node{object_type, object_id,
node_id, clazz_name}].
"""

import base64
import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_GT = """
mutation ($created: DateTime!, $title: String!) {
  create_general_task(input: {
    created: $created
    title: $title
    description: "iterate-items"
    agent_name: "tester"
  }) { general_task { id } }
}
"""

QUERY_OBJECT_IDENTITIES = """
query ($object_type: String!, $first: Int, $after: String) {
  object_identities(object_type: $object_type, first: $first, after: $after) {
    pageInfo {
      endCursor
      hasNextPage
    }
    edges {
      cursor
      node {
        __typename
        object_type
        object_id
        node_id
        clazz_name
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def seeded_ids(gql_context):
    """Seed 5 GeneralTasks so pagination has something to bite on."""
    created = dt.datetime.now(tzutc()).isoformat()
    ids = []
    for i in range(5):
        res = schema.execute_sync(
            CREATE_GT,
            variable_values={"created": created, "title": f"iterate-{i}"},
            context_value=gql_context,
        )
        assert res.errors is None, res.errors
        ids.append(res.data["create_general_task"]["general_task"]["id"])
    return ids


def test_object_identities_returns_edges(seeded_ids, gql_context):
    """Asking for first:3 returns 3 edges."""
    res = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "GeneralTask", "first": 3, "after": None},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    conn = res.data["object_identities"]
    assert len(conn["edges"]) == 3


def test_object_identities_edge_node_shape(seeded_ids, gql_context):
    """Edge.node has object_type, object_id, node_id, clazz_name."""
    res = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "GeneralTask", "first": 3, "after": None},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    node = res.data["object_identities"]["edges"][0]["node"]
    assert node["object_type"] == "GeneralTask"
    assert node["clazz_name"] == "GeneralTask"
    assert node["object_id"]
    # node_id is a Relay-encoded GlobalID
    assert node["node_id"].startswith("R2VuZXJhbFRhc2s6")
    decoded = base64.b64decode(node["node_id"]).decode()
    assert decoded.startswith("GeneralTask:")


def test_object_identities_pagination_has_next_page(seeded_ids, gql_context):
    """With 5 items seeded and first:3, hasNextPage is true."""
    res = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "GeneralTask", "first": 3, "after": None},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    page_info = res.data["object_identities"]["pageInfo"]
    assert page_info["hasNextPage"] is True
    assert page_info["endCursor"] is not None


def test_object_identities_after_cursor_returns_next_page(seeded_ids, gql_context):
    """Passing the previous endCursor returns the next batch (no duplicates)."""
    first = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "GeneralTask", "first": 3, "after": None},
        context_value=gql_context,
    )
    assert first.errors is None, first.errors
    cursor = first.data["object_identities"]["pageInfo"]["endCursor"]
    first_ids = {e["node"]["object_id"] for e in first.data["object_identities"]["edges"]}

    second = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "GeneralTask", "first": 10, "after": cursor},
        context_value=gql_context,
    )
    assert second.errors is None, second.errors
    second_ids = {e["node"]["object_id"] for e in second.data["object_identities"]["edges"]}
    # No overlap between batches
    assert first_ids.isdisjoint(second_ids), f"page-1 and page-2 ids overlap: {first_ids & second_ids}"


def test_object_identities_unknown_type_returns_empty(seeded_ids, gql_context):
    """A type we never seeded returns an empty edges list, not an error."""
    res = schema.execute_sync(
        QUERY_OBJECT_IDENTITIES,
        variable_values={"object_type": "ThisTypeDoesNotExist", "first": 3, "after": None},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    assert res.data["object_identities"]["edges"] == []
