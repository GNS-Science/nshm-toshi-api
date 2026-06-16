"""Ported from graphql_api/tests/test_table_schema.py.

POC's `test_bugfix_252_table_create.py` already covers the create path.
This port adds the legacy `test_get_table_by_node_id` coverage —
node-lookup of a Table with `rows`, `meta`, `dimensions`, `table_type`
all selected. Exercises the `Table.rows: list[list[str | None] | None]`
read path which had no test coverage.
"""

import pytest

from graphql_api.schema import schema


CREATE_TABLE = """
mutation (
  $object_id: ID!,
  $column_headers: [String],
  $column_types: [RowItemType],
  $rows: [[String]],
  $meta: [KeyValuePairInput],
  $dimensions: [KeyValueListPairInput],
) {
  create_table(input: {
    object_id: $object_id
    created: "2021-06-11T02:37:26.009506+00:00"
    column_headers: $column_headers
    column_types: $column_types
    rows: $rows
    meta: $meta
    table_type: HAZARD_GRIDDED
    dimensions: $dimensions
  })
  {
    table {
      id
      column_headers
      column_types
      rows
      meta { k v }
      dimensions { k v }
      table_type
    }
  }
}
"""

NODE_QUERY = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on Table {
      id
      object_id
      column_headers
      column_types
      rows
      meta { k v }
      dimensions { k v }
      table_type
    }
  }
}
"""


@pytest.fixture(scope="module")
def created(gql_context):
    res = schema.execute_sync(
        CREATE_TABLE,
        variable_values={
            "object_id": "R2VuZXJhbFRhc2s6MjE3Qk1YREw=",
            "column_headers": ["OK", "DOKEY"],
            "column_types": ["integer", "double"],
            "rows": [["1", "1.01"], ["2", "2.2"]],
            "meta": [
                {"k": "round", "v": "0"},
                {"k": "config_type", "v": "crustal"},
            ],
            "dimensions": [
                {"k": "grid_spacings", "v": ["0.1"]},
                {"k": "IML_periods", "v": ["0", "0.1"]},
                {"k": "tags", "v": ["opensha", "testing"]},
                {"k": "gmpes", "v": ["ASK_2014"]},
            ],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_table"]["table"]


def test_create_returns_full_payload(created):
    """Create mutation echoes back everything we sent."""
    assert created["id"]
    assert created["column_headers"] == ["OK", "DOKEY"]
    assert created["column_types"] == ["integer", "double"]
    assert created["rows"] == [["1", "1.01"], ["2", "2.2"]]
    assert created["table_type"] == "HAZARD_GRIDDED"


def test_node_lookup_returns_rows(created, gql_context):
    """node(id:) returns the full rows back. The Table.rows[list[list[str|None]|None]|None]
    read path has no other test coverage in POC.
    """
    res = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created["id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    node = res.data["node"]
    assert node["rows"] == [["1", "1.01"], ["2", "2.2"]]


def test_node_lookup_returns_dimensions(created, gql_context):
    """dimensions list-of-KeyValueListPair survives the node lookup."""
    res = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created["id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    dims = {d["k"]: d["v"] for d in res.data["node"]["dimensions"]}
    assert dims["grid_spacings"] == ["0.1"]
    assert dims["IML_periods"] == ["0", "0.1"]
    assert dims["tags"] == ["opensha", "testing"]


def test_node_lookup_returns_meta(created, gql_context):
    """meta list-of-KeyValuePair survives the node lookup."""
    res = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created["id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    meta = {m["k"]: m["v"] for m in res.data["node"]["meta"]}
    assert meta["round"] == "0"
    assert meta["config_type"] == "crustal"


def test_node_lookup_returns_table_type(created, gql_context):
    """Enum round-trips via node lookup."""
    res = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created["id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    assert res.data["node"]["table_type"] == "HAZARD_GRIDDED"
