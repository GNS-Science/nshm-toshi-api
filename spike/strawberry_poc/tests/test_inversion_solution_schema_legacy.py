"""Ported from graphql_api/tests/test_inversion_solution_schema.py.

Exercises #322's surface on InversionSolution:
  - `create_inversion_solution(input: { mfd_table_id: ... })` — new input field
  - `InversionSolution.mfd_table { id }`, `.hazard_table { id }` — Table resolvers
  - `InversionSolution.mfd_table_id`, `.hazard_table_id` — ID fields
  - `LabelledTableRelation.table { id }` — new resolver
  - `tables { identity, table_id, table_type, label, dimensions, table { id } }`

Legacy tests mocked DynamoDB reads; this port seeds via real mutations.
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from schema import schema


CREATE_TABLE = """
mutation ($name: String, $object_id: ID!, $rows: [[String]], $column_headers: [String], $column_types: [RowItemType]) {
  create_table(input: {
    name: $name
    object_id: $object_id
    rows: $rows
    column_headers: $column_headers
    column_types: $column_types
    table_type: MFD_CURVES_V2
  }) {
    table { id }
  }
}
"""

CREATE_HAZARD_TABLE = """
mutation ($name: String, $object_id: ID!) {
  create_table(input: {
    name: $name
    object_id: $object_id
    rows: [["0.1","0.2"]]
    column_headers: ["x","y"]
    column_types: [double, double]
    table_type: HAZARD_GRIDDED
  }) {
    table { id }
  }
}
"""

CREATE_GT = """
mutation ($created: DateTime!) {
  create_general_task(input:{
    created: $created
    title: "host"
    description: "host"
    agent_name: "tester"
  })
  { general_task { id } }
}
"""

CREATE_AT = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    created: $created
    duration: 1
    task_type: INVERSION
  })
  { task_result { id } }
}
"""

CREATE_INVERSION = """
mutation (
  $file_name: String!,
  $md5: String!,
  $size: BigInt!,
  $produced_by: ID!,
  $created: DateTime!,
  $mfd_table_id: ID!,
  $hazard_table_id: ID!,
) {
  create_inversion_solution(input: {
    file_name: $file_name
    md5_digest: $md5
    file_size: $size
    produced_by: $produced_by
    created: $created
    mfd_table_id: $mfd_table_id
    hazard_table_id: $hazard_table_id
    metrics: [{ k: "total_perturbations", v: "1889" }]
    tables: [
      {
        table_id: $mfd_table_id
        table_type: MFD_CURVES_V2
        label: "mfd-curves"
      }
      {
        table_id: $hazard_table_id
        table_type: HAZARD_GRIDDED
        label: "hazard-grid"
        dimensions: [
          { k: "grid_spacings", v: ["0.1"] }
          { k: "tags", v: ["opensha", "testing"] }
        ]
      }
    ]
  }) {
    inversion_solution { id }
  }
}
"""

QUERY_RESOLVED_FIELDS = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on InversionSolution {
      id
      file_name
      mfd_table_id
      mfd_table { id }
      hazard_table_id
      hazard_table { id }
      metrics { k v }
      tables {
        identity
        table_id
        table_type
        label
        dimensions { k v }
        table { id }
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def seeded(gql_context):
    created = dt.datetime.now(tzutc()).isoformat()

    # Seed an MFD table
    mfd = schema.execute_sync(
        CREATE_TABLE,
        variable_values={
            "name": "mfd",
            "object_id": "mfd-1",
            "rows": [["1.0", "2.0"]],
            "column_headers": ["a", "b"],
            "column_types": ["double", "double"],
        },
        context_value=gql_context,
    )
    assert mfd.errors is None, mfd.errors
    mfd_id = mfd.data["create_table"]["table"]["id"]

    # Seed a hazard table
    hazard = schema.execute_sync(
        CREATE_HAZARD_TABLE,
        variable_values={"name": "hazard", "object_id": "haz-1"},
        context_value=gql_context,
    )
    assert hazard.errors is None, hazard.errors
    hazard_id = hazard.data["create_table"]["table"]["id"]

    # Seed parent task for produced_by
    at = schema.execute_sync(CREATE_AT, variable_values={"created": created}, context_value=gql_context)
    assert at.errors is None, at.errors
    at_id = at.data["create_automation_task"]["task_result"]["id"]

    # Create the inversion solution wiring everything together
    inv = schema.execute_sync(
        CREATE_INVERSION,
        variable_values={
            "file_name": "MyInversion.zip",
            "md5": "ABC",
            "size": 1000,
            "produced_by": at_id,
            "created": created,
            "mfd_table_id": mfd_id,
            "hazard_table_id": hazard_id,
        },
        context_value=gql_context,
    )
    assert inv.errors is None, inv.errors
    inv_id = inv.data["create_inversion_solution"]["inversion_solution"]["id"]

    return {"inv_id": inv_id, "mfd_id": mfd_id, "hazard_id": hazard_id}


def test_inversion_resolved_fields(seeded, gql_context):
    """Ported from legacy test_get_inversion_solution_resolved_by_id_fields.
    Exercises mfd_table/hazard_table resolvers + tables[].table.
    """
    res = schema.execute_sync(
        QUERY_RESOLVED_FIELDS, variable_values={"id": seeded["inv_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    node = res.data["node"]
    assert node["__typename"] == "InversionSolution"
    assert node["id"] == seeded["inv_id"]
    assert node["mfd_table_id"] == seeded["mfd_id"]
    assert node["mfd_table"]["id"] == seeded["mfd_id"]
    assert node["hazard_table_id"] == seeded["hazard_id"]
    assert node["hazard_table"]["id"] == seeded["hazard_id"]


def test_inversion_tables_table_resolver(seeded, gql_context):
    """LabelledTableRelation.table resolver populated (#322 added it)."""
    res = schema.execute_sync(
        QUERY_RESOLVED_FIELDS, variable_values={"id": seeded["inv_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    tables = res.data["node"]["tables"]
    table_ids = sorted(t["table"]["id"] for t in tables if t["table"])
    assert seeded["mfd_id"] in table_ids
    assert seeded["hazard_id"] in table_ids


def test_inversion_tables_dimensions_round_trip(seeded, gql_context):
    """LabelledTableRelation.dimensions list-of-KeyValueListPair preserved."""
    res = schema.execute_sync(
        QUERY_RESOLVED_FIELDS, variable_values={"id": seeded["inv_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    hazard_entry = next(t for t in res.data["node"]["tables"] if t["table_type"] == "HAZARD_GRIDDED")
    dims = {d["k"]: d["v"] for d in hazard_entry["dimensions"]}
    assert dims["grid_spacings"] == ["0.1"]
    assert dims["tags"] == ["opensha", "testing"]


def test_inversion_metrics_round_trip(seeded, gql_context):
    """metrics is list-of-KeyValuePair output — list nullability #322."""
    res = schema.execute_sync(
        QUERY_RESOLVED_FIELDS, variable_values={"id": seeded["inv_id"]}, context_value=gql_context
    )
    assert res.errors is None, res.errors
    metrics = {m["k"]: m["v"] for m in res.data["node"]["metrics"]}
    assert metrics["total_perturbations"] == "1889"
