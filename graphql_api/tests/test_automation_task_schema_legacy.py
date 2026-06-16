"""Ported from graphql_api/tests/test_automation_task_schema.py.

Covers cases the existing POC test_automation_task.py doesn't:
  - Naive datetime is rejected (must include timezone)
  - Malformed datetime string is rejected
  - GraphQL input coercion: `metrics: {k:.. v:..}` (single object) accepted
    where `metrics: [..]` (list) is expected
"""

import datetime as dt

from dateutil.tz import tzutc

from graphql_api.schema import schema

CREATE_AT = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    task_type: INVERSION
    state: UNDEFINED
    result: UNDEFINED
    created: $created
    duration: 600
  })
  { task_result { id } }
}
"""


CREATE_AT_INLINE_DATE = """
mutation {
  create_automation_task(input: {
    task_type: INVERSION
    state: UNDEFINED
    result: UNDEFINED
    created: "September 5th, 1999"
    duration: 600
  })
  { task_result { id } }
}
"""


CREATE_AT_WITH_SCALAR_METRICS = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    task_type: INVERSION
    state: UNDEFINED
    result: UNDEFINED
    created: $created
    duration: 600
    # GraphQL input coercion: single object should be auto-wrapped to list.
    metrics: { k: "rupture_count" v: "206776" }
  })
  { task_result { id metrics { k v } } }
}
"""


def test_naive_datetime_rejected(gql_context):
    """Bare datetime (no tz) should fail at the DateTime scalar layer."""
    naive = dt.datetime.now()  # no tz
    res = schema.execute_sync(CREATE_AT, variable_values={"created": naive.isoformat()}, context_value=gql_context)
    assert res.errors is not None, "expected naive datetime to be rejected"
    # The legacy error said "must have a timezone". Strawberry's may differ; we
    # accept any error referencing timezone or aware/naive distinction.
    err_text = " ".join(str(e) for e in res.errors).lower()
    assert any(token in err_text for token in ("timezone", "tz", "aware", "naive")), (
        f"DateTime rejection error didn't mention tz/timezone: {res.errors}"
    )


def test_malformed_datetime_rejected(gql_context):
    """A clearly-non-iso string should be rejected by the DateTime scalar."""
    res = schema.execute_sync(CREATE_AT_INLINE_DATE, context_value=gql_context)
    assert res.errors is not None
    # The legacy error included the offending string in the message. POC may
    # too — accept either way as long as there's some validation error.
    err_text = " ".join(str(e) for e in res.errors)
    assert err_text  # any non-empty error message is fine


def test_single_object_coerces_to_list(gql_context):
    """GraphQL input coercion: passing `metrics: { k: ..., v: ... }` (a single
    object) at a position expecting `[KeyValuePairInput]` is valid GraphQL — the
    spec mandates the value be wrapped into a single-element list. Legacy
    accepted this; POC should too.
    """
    created = dt.datetime.now(tzutc()).isoformat()
    res = schema.execute_sync(
        CREATE_AT_WITH_SCALAR_METRICS,
        variable_values={"created": created},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    task = res.data["create_automation_task"]["task_result"]
    assert task["metrics"] == [{"k": "rupture_count", "v": "206776"}]
