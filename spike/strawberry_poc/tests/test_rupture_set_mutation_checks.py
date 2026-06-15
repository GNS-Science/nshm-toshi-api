"""Ported from graphql_api/tests/rupture_set/test_rupture_set_mutation_checks.py.

Exercises input-validation behaviour on create_rupture_set:
  - Missing required fields surface in the error messages
  - Bad `created` values rejected by the DateTime scalar (#6)
  - Bad `fault_models` types rejected at validation
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from schema import schema


CREATE_RS_BARE = """
mutation ($created: DateTime!) {
  create_rupture_set(input: {
    created: $created
  }) {
    rupture_set { id }
  }
}
"""

CREATE_RS = """
mutation (
  $created: DateTime!,
  $md5: String!,
  $file_name: String!,
  $file_size: BigInt!,
  $produced_by: ID!,
  $fault_models: [String],
) {
  create_rupture_set(input: {
    created: $created
    md5_digest: $md5
    file_name: $file_name
    file_size: $file_size
    produced_by: $produced_by
    fault_models: $fault_models
  }) {
    rupture_set { id file_name fault_models }
  }
}
"""

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


@pytest.fixture(scope="module")
def producer_id(gql_context):
    """create_rupture_set requires produced_by to be a RuptureGenerationTask."""
    res = schema.execute_sync(
        CREATE_RGT,
        variable_values={"created": dt.datetime.now(tzutc()).isoformat()},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_rupture_generation_task"]["task_result"]["id"]


def _assert_error_mentions(errors, expected):
    """At least one of the GraphQL errors must mention `expected`."""
    text = " ".join(str(e) for e in errors)
    assert expected in text, f"expected `{expected}` in errors, got: {text}"


def test_missing_required_file_attributes_fails(gql_context):
    """Calling create_rupture_set with only `created` must fail on each missing field."""
    res = schema.execute_sync(
        CREATE_RS_BARE,
        variable_values={"created": dt.datetime.now(tzutc()).isoformat()},
        context_value=gql_context,
    )
    assert res.errors is not None
    # Combine all error messages and check each missing field is referenced
    text = " ".join(str(e) for e in res.errors)
    for required in ("file_name", "file_size", "md5_digest"):
        assert required in text, f"missing-field error didn't mention {required}: {text}"


@pytest.mark.parametrize(
    "created_value, expect_ok",
    [
        (dt.datetime.now(tzutc()).isoformat(), True),
        ("", False),
        ("can't parse this as a date", False),
        # An integer should fail at the DateTime scalar layer.
        (1001, False),
    ],
)
def test_created_value_validation(gql_context, producer_id, created_value, expect_ok):
    """The DateTime scalar (#6) rejects invalid values; valid tz-aware strings pass."""
    res = schema.execute_sync(
        CREATE_RS,
        variable_values={
            "created": created_value,
            "md5": "digest",
            "file_name": "rs.zip",
            "file_size": 1000,
            "produced_by": producer_id,
            "fault_models": ["A", "B"],
        },
        context_value=gql_context,
    )
    if expect_ok:
        assert res.errors is None, res.errors
        assert res.data["create_rupture_set"]["rupture_set"]["file_name"] == "rs.zip"
    else:
        assert res.errors is not None, f"expected error for created={created_value!r}"


def test_fault_models_int_rejected(gql_context, producer_id):
    """Passing an int where [String] is expected fails at GraphQL validation."""
    res = schema.execute_sync(
        CREATE_RS,
        variable_values={
            "created": dt.datetime.now(tzutc()).isoformat(),
            "md5": "digest",
            "file_name": "rs.zip",
            "file_size": 1000,
            "produced_by": producer_id,
            "fault_models": 1001,
        },
        context_value=gql_context,
    )
    assert res.errors is not None
    _assert_error_mentions(res.errors, "fault_models")


def test_fault_models_happy_path(gql_context, producer_id):
    """`fault_models: ["A", "B"]` is accepted and round-trips."""
    res = schema.execute_sync(
        CREATE_RS,
        variable_values={
            "created": dt.datetime.now(tzutc()).isoformat(),
            "md5": "digest",
            "file_name": "rs.zip",
            "file_size": 1000,
            "produced_by": producer_id,
            "fault_models": ["ModelA", "ModelB"],
        },
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    rs = res.data["create_rupture_set"]["rupture_set"]
    assert rs["fault_models"] == ["ModelA", "ModelB"]
