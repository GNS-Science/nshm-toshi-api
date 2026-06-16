"""Ported from graphql_api/tests/test_file_relation_bugfix_126.py.

Exercises:
  - `create_file_relation(file_id:, role:, thing_id:)` positional (#322)
  - `CreateFileRelationPayload { ok, file_relation { file_id thing_id role } }`
    — file_relation field on the payload (legacy parity gap caught by this port)
  - `FileRelation.file_id` / `FileRelation.thing_id` as public Strings
    (sibling to TaskTaskRelation.parent_id / child_id)
"""

import datetime as dt

import pytest
from dateutil.tz import tzutc

from graphql_api.schema import schema


CREATE_AT = """
mutation ($created: DateTime!) {
  create_automation_task(input: {
    state: UNDEFINED
    result: UNDEFINED
    task_type: INVERSION
    created: $created
    duration: 600
  })
  { task_result { id } }
}
"""

CREATE_FILE = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size) {
    ok
    file_result { id }
  }
}
"""

CREATE_AT_RELATION = """
mutation ($thing_id: ID!, $file_id: ID!) {
  create_file_relation(
    thing_id: $thing_id
    file_id: $file_id
    role: READ
  )
  {
    ok
    file_relation {
      file_id
      thing_id
      role
    }
  }
}
"""


@pytest.fixture(scope="module")
def at_id(gql_context):
    created = dt.datetime.now(tzutc()).isoformat()
    res = schema.execute_sync(CREATE_AT, variable_values={"created": created}, context_value=gql_context)
    assert res.errors is None, res.errors
    return res.data["create_automation_task"]["task_result"]["id"]


@pytest.fixture(scope="module")
def file_id(gql_context):
    res = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "ruptset.zip", "md5": "abcd", "size": 32045903},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    return res.data["create_file"]["file_result"]["id"]


def test_create_file_relation_returns_ok(at_id, file_id, gql_context):
    """create_file_relation positional mutation returns ok=true."""
    res = schema.execute_sync(
        CREATE_AT_RELATION,
        variable_values={"thing_id": at_id, "file_id": file_id},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    assert res.data["create_file_relation"]["ok"] is True


def test_create_file_relation_payload_includes_file_relation(at_id, file_id, gql_context):
    """Legacy parity: payload exposes `file_relation { file_id thing_id role }`."""
    res = schema.execute_sync(
        CREATE_AT_RELATION,
        variable_values={"thing_id": at_id, "file_id": file_id},
        context_value=gql_context,
    )
    assert res.errors is None, res.errors
    fr = res.data["create_file_relation"]["file_relation"]
    assert fr is not None
    assert fr["role"] == "READ"
    # IDs come back as raw (post-decoded) — they're the underlying object IDs.
    assert fr["file_id"] is not None
    assert fr["thing_id"] is not None
