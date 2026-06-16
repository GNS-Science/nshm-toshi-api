"""Ported from graphql_api/tests/test_inversion_solution_bug_93.py.

Bug #93: when an AutomationTask has multiple WRITE-role file relations,
the `inversion_solution` resolver must SKIP files whose clazz_name isn't
an InversionSolution subtype, not return the first WRITE file.

POC's test_weka_parity.py covers the simple case (one WRITE file = IS)
and the no-write case. This port adds the discriminating case from the
original production bug.
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
    duration: 97
  }) { task_result { id } }
}
"""

CREATE_FILE = """
mutation ($file_name: String!, $md5: String!, $size: BigInt!) {
  create_file(file_name: $file_name, md5_digest: $md5, file_size: $size) {
    file_result { id }
  }
}
"""

CREATE_INVERSION = """
mutation ($file_name: String!, $produced_by: ID!, $md5: String!, $size: BigInt!, $created: DateTime!) {
  create_inversion_solution(input: {
    file_name: $file_name
    produced_by: $produced_by
    md5_digest: $md5
    file_size: $size
    created: $created
  }) { inversion_solution { id } }
}
"""

CREATE_FILE_RELATION = """
mutation ($thing_id: ID!, $file_id: ID!, $role: FileRole!) {
  create_file_relation(thing_id: $thing_id, file_id: $file_id, role: $role) { ok }
}
"""

QUERY_AT_INVERSION = """
query ($id: ID!) {
  node(id: $id) {
    __typename
    ... on AutomationTask {
      id
      inversion_solution {
        __typename
        ... on Node { id }
        ... on FileInterface { file_name }
      }
    }
  }
}
"""


@pytest.fixture(scope="module")
def scenario(gql_context):
    """Replicate bug #93's data shape:
      - 1 AutomationTask
      - 1 READ file (plain File)
      - 1 WRITE file (plain File, NOT an InversionSolution)
      - 1 WRITE file (InversionSolution)
    Resolver must return the IS, not the plain WRITE File.
    """
    created = dt.datetime.now(tzutc()).isoformat()

    at = schema.execute_sync(CREATE_AT, variable_values={"created": created}, context_value=gql_context)
    assert at.errors is None, at.errors
    at_id = at.data["create_automation_task"]["task_result"]["id"]

    read_file = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "input.csv", "md5": "rrrr", "size": 100},
        context_value=gql_context,
    )
    assert read_file.errors is None, read_file.errors
    read_id = read_file.data["create_file"]["file_result"]["id"]

    write_other = schema.execute_sync(
        CREATE_FILE,
        variable_values={"file_name": "Wellington.geojson", "md5": "wwww", "size": 725970},
        context_value=gql_context,
    )
    assert write_other.errors is None, write_other.errors
    write_other_id = write_other.data["create_file"]["file_result"]["id"]

    inv = schema.execute_sync(
        CREATE_INVERSION,
        variable_values={
            "file_name": "solution.zip",
            "produced_by": at_id,
            "md5": "iiii",
            "size": 29144881,
            "created": created,
        },
        context_value=gql_context,
    )
    assert inv.errors is None, inv.errors
    inv_id = inv.data["create_inversion_solution"]["inversion_solution"]["id"]

    for file_id, role in [(read_id, "READ"), (write_other_id, "WRITE"), (inv_id, "WRITE")]:
        rel = schema.execute_sync(
            CREATE_FILE_RELATION,
            variable_values={"thing_id": at_id, "file_id": file_id, "role": role},
            context_value=gql_context,
        )
        assert rel.errors is None, rel.errors

    return {"at_id": at_id, "read_id": read_id, "write_other_id": write_other_id, "inv_id": inv_id}


def test_inversion_solution_skips_non_is_write_files(scenario, gql_context):
    """Bug #93 regression: with multiple WRITE files, only the IS is selected."""
    res = schema.execute_sync(QUERY_AT_INVERSION, variable_values={"id": scenario["at_id"]}, context_value=gql_context)
    assert res.errors is None, res.errors
    sol = res.data["node"]["inversion_solution"]
    assert sol is not None
    assert sol["__typename"] == "InversionSolution"
    assert sol["id"] == scenario["inv_id"]
    assert sol["file_name"] == "solution.zip"


def test_inversion_solution_not_the_non_is_write_file(scenario, gql_context):
    """Explicit assertion the resolver did NOT return the plain WRITE File."""
    res = schema.execute_sync(QUERY_AT_INVERSION, variable_values={"id": scenario["at_id"]}, context_value=gql_context)
    assert res.errors is None, res.errors
    sol = res.data["node"]["inversion_solution"]
    assert sol["id"] != scenario["write_other_id"]
    assert sol["id"] != scenario["read_id"]
