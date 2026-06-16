"""
Tests for create_file file_size type coercion / validation.

Covers COVERAGE_GAPS.md gap 8 (mirrors legacy test_create_file_bugfix_159.py
which exercised file_size as BigInt, float, int, string).

file_size uses the custom BigInt scalar (see models/common.py) so values
exceeding GraphQL's 32-bit Int limit (>2GB) round-trip correctly.
"""

from graphql_api.schema import schema

MAX_INT32 = 2**31 - 1  # 2_147_483_647

CREATE_FILE_MUTATION = """
mutation($file_name: String!, $md5_digest: String!, $file_size: BigInt!, $created: DateTime = null, $meta: [KeyValuePairInput!] = null) {
    create_file(file_name: $file_name, md5_digest: $md5_digest, file_size: $file_size, created: $created, meta: $meta) {
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
                "file_name": "small.zip",
                "md5_digest": "00",
                "file_size": 1024,
                "created": "2024-05-01T00:00:00Z",
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
                "file_name": "near_max.zip",
                "md5_digest": "01a",
                "file_size": MAX_INT32,
                "created": "2024-05-01T00:00:00Z",
            },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_file"]["file_result"]["file_size"] == MAX_INT32


def test_create_file_with_large_file_size_bigint(gql_context):
    """5GB file_size (> 32-bit int) round-trips correctly via the BigInt scalar."""
    big = 5_000_000_000
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
                "file_name": "big.zip",
                "md5_digest": "01",
                "file_size": big,
                "created": "2024-05-01T00:00:00Z",
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
                "file_name": "bad.zip",
                "md5_digest": "02",
                "file_size": "not-a-number",
                "created": "2024-05-01T00:00:00Z",
            },
        context_value=gql_context,
    )
    assert result.errors is not None
    assert any("file_size" in str(e).lower() or "int" in str(e).lower() for e in result.errors)


def test_create_file_rejects_missing_file_size(gql_context):
    """file_size omitted is rejected — the field is required (matches legacy SDL).

    Previously this test asserted the opposite (POC had file_size as nullable),
    but legacy SDL has `file_size: BigInt!`. After the positional-args
    realignment (PR-after-#320), POC follows suit.
    """
    result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "file_name": "nofsize.zip",
            "md5_digest": "03",
            "created": "2024-05-01T00:00:00Z",
        },
        context_value=gql_context,
    )
    assert result.errors is not None
    assert any("file_size" in str(e) for e in result.errors)
