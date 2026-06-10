"""Regression test for legacy bug #252 — table creation from runzi.

Ports `graphql_api/tests/test_table_schema_fix_252.py`. The original bug
was a Graphene-side enum serialisation error ("Object of type EnumMeta is
not JSON serializable") when runzi sent the canonical create_table
mutation with `column_types: [RowItemType]!` and a `dimensions` payload.

The exact mutation shape comes from production runzi:
https://github.com/GNS-Science/nzshm-runzi/blob/8c390a34d3a803fd357846aadfce21b891c9d299/runzi/automation/scaling/toshi_api/toshi_api.py#L250-L274

The POC's `RowItemType` enum and `column_types` field were added in the
weka-parity work specifically to keep this contract alive — this test
pins it.
"""

from schema import schema

CREATE_TABLE = """
mutation CreateTable(
    $rows: [[String!]!]!,
    $object_id: ID!,
    $table_name: String!,
    $headers: [String!]!,
    $column_types: [RowItemType!]!,
    $created: DateTime!,
    $table_type: TableType!,
    $dimensions: [KeyValueListPairInput!]!
) {
    create_table(input: {
        name: $table_name
        created: $created
        table_type: $table_type
        dimensions: $dimensions
        object_id: $object_id
        column_headers: $headers
        column_types: $column_types
        rows: $rows
    }) {
        table { id }
    }
}
"""

CREATE_THING = """
mutation CreateThing($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) { task_result { id } }
}
"""


def test_create_table_runzi_shape(gql_context):
    # Seed a parent thing whose ID is the object_id for the table.
    thing = schema.execute_sync(
        CREATE_THING,
        variable_values={
            "input": {
                "state": "UNDEFINED",
                "result": "UNDEFINED",
                "task_type": "INVERSION",
                "created": "2026-01-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert thing.errors is None, thing.errors
    parent_id = thing.data["create_automation_task"]["task_result"]["id"]

    # Exact shape from nzshm-runzi.
    variables = {
        "headers": ["series", "series_name", "X", "Y"],
        "object_id": parent_id,
        "rows": [["0", "foo", "1.0", "2.0"], ["1", "bar", "1.5", "2.5"]],
        "column_types": ["integer", "string", "double", "double"],
        "table_name": "Inversion Solution MFD table",
        "created": "2026-01-01T00:00:00Z",
        "table_type": "MFD_CURVES",
        "dimensions": [],
    }

    res = schema.execute_sync(CREATE_TABLE, variable_values=variables, context_value=gql_context)
    assert res.errors is None, res.errors
    assert res.data["create_table"]["table"]["id"]
