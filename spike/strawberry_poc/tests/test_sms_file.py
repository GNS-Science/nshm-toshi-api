"""Tests for SmsFile — create and node lookup."""

import base64

import pytest

from schema import schema

# ── GQL strings ───────────────────────────────────────────────────────────────

CREATE_MUTATION = """
mutation CreateSmsFile($input: CreateSmsFileInput!) {
    create_sms_file(input: $input) {
        ok
        file_result {
            id
            file_name
            file_size
            md5_digest
            created
            file_type
        }
    }
}
"""

NODE_QUERY = """
query GetSmsFile($id: ID!) {
    node(id: $id) {
        id
        ... on SmsFile {
            file_name
            file_type
        }
    }
}
"""


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def created_sms_file(gql_context):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "borehole_log.csv",
                "file_type": "BH",
                "md5_digest": "abcdef12",
                "file_size": 8192,
                "created": "2024-07-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_sms_file"]["file_result"]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_create_returns_id(created_sms_file):
    gid = created_sms_file["id"]
    decoded = base64.b64decode(gid).decode()
    assert decoded.startswith("SmsFile:"), decoded


def test_create_ok(gql_context):
    result = schema.execute_sync(
        CREATE_MUTATION,
        variable_values={
            "input": {
                "file_name": "hvsr_data.csv",
                "file_type": "HVSR",
                "created": "2024-07-02T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    assert result.data["create_sms_file"]["ok"] is True


def test_fields(created_sms_file):
    f = created_sms_file
    assert f["file_name"] == "borehole_log.csv"
    assert f["file_type"] == "BH"
    assert f["md5_digest"] == "abcdef12"
    assert f["file_size"] == 8192
    assert f["created"] == "2024-07-01T00:00:00Z"


def test_node_lookup(created_sms_file, gql_context):
    result = schema.execute_sync(NODE_QUERY, variable_values={"id": created_sms_file["id"]}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["file_name"] == "borehole_log.csv"
    assert node["file_type"] == "BH"
