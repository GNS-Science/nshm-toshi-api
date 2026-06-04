"""
Tests for create_file file_size type coercion / validation.

Covers COVERAGE_GAPS.md gap 8 (mirrors legacy test_create_file_bugfix_159.py
which exercised file_size as BigInt, float, int, string).

In the POC, file_size is typed as `int | None` (Strawberry's Int scalar — 32-bit).
The legacy schema used a BigInt scalar so values >2GB worked; the POC inherits
GraphQL's 32-bit Int limit until a BigInt scalar is added. The xfail test
below pins this known limitation so it's visible in the test report.
"""

import pytest

from schema import schema

MAX_INT32 = 2**31 - 1  # 2_147_483_647

CREATE_FILE_MUTATION = """
mutation($input: CreateFileInput!) {
    create_file(input: $input) {
        ok
        file_result {
            id
            file_name
            file_size
        }
    }
}
"""


def test_create_file_with_int_file_size(gql_context):
    """Standard small file_size as int — round-trips correctly."""
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "small.zip",
                "md5_digest": "00",
                "file_size": 1024,
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file"]["file_result"]["file_size"] == 1024


def test_create_file_with_max_int32_file_size(gql_context):
    """file_size up to MAX_INT32 (~2GB) round-trips through GraphQL Int."""
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "near_max.zip",
                "md5_digest": "01a",
                "file_size": MAX_INT32,
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file"]["file_result"]["file_size"] == MAX_INT32


@pytest.mark.xfail(
    reason="POC file_size uses GraphQL Int (32-bit); BigInt scalar not yet added.",
    strict=True,
)
def test_create_file_with_large_file_size_bigint(gql_context):
    """5GB file_size (> 32-bit int) — should round-trip when BigInt scalar is added.

    Known limitation: the POC inherits GraphQL's 32-bit Int. Legacy schema used
    a BigInt scalar. Marked xfail so the gap is visible until a BigInt scalar
    is added across all file_size fields (file.py, file_interface.py, and 9
    other model files).
    """
    big = 5_000_000_000
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "big.zip",
                "md5_digest": "01",
                "file_size": big,
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file"]["file_result"]["file_size"] == big


def test_create_file_rejects_string_file_size(gql_context):
    """Non-numeric string for file_size must surface as a GraphQL validation error."""
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "bad.zip",
                "md5_digest": "02",
                "file_size": "not-a-number",
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is not None
    assert any("file_size" in str(e).lower() or "int" in str(e).lower() for e in result.errors)


def test_create_file_with_null_file_size(gql_context):
    """file_size omitted (null) is acceptable; the field is optional."""
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "input": {
                "file_name": "nofsize.zip",
                "md5_digest": "03",
                "created": "2024-05-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file"]["file_result"]["file_size"] is None
