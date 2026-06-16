"""Regression test for legacy bug #217 — `subtask_type` + `model_type` on GeneralTask.

Ports `graphql_api/tests/test_general_task_bugfix_217.py`. The original bug
was that the enum values OPENQUAKE_HAZARD / COMPOSITE were not round-tripping
correctly through Graphene's enum coercion when paired with the
`argument_lists` key-value-list payload. Pin the contract here so a future
Strawberry enum refactor doesn't reintroduce the same shape.
"""

from graphql_api.schema import schema

CREATE_GT = """
mutation CreateGT($created: DateTime!) {
    create_general_task(input: {
        created: $created
        title: "TEST Build opensha rupture set Coulomb #1"
        description: "Using "
        agent_name: "chrisbc"
        subtask_type: OPENQUAKE_HAZARD
        model_type: COMPOSITE
        argument_lists: [{k: "some_metric", v: ["20", "25"]}]
    }) {
        general_task {
            id
            subtask_type
            model_type
        }
    }
}
"""


def test_create_general_task_with_subtype_and_model_type(gql_context):
    res = schema.execute_sync(
        CREATE_GT,
        variable_values={"created": "2026-01-01T00:00:00Z"},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    gt = res.data["create_general_task"]["general_task"]
    assert gt["id"]
    assert gt["subtask_type"] == "OPENQUAKE_HAZARD"
    assert gt["model_type"] == "COMPOSITE"
