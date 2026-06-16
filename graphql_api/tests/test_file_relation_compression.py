"""
Tests for File.relations compression behaviour.

Mirrors graphql_api/tests/test_file_relation_compression.py — when the
relations list crosses UNCOMPRESSED_LIMIT entries, the data layer stores
it as a compressed string instead of a JSON list. The same nzshm_common
compress_string is used so this format is byte-compatible with the
legacy production data layer.

Covers COVERAGE_GAPS.md gap 6 (re-categorised from "Low/N/A" to "High"
once we noticed that the POC would crash on legacy compressed rows and
would hit DynamoDB's 400KB item limit at ~10k uncompressed relations).
"""

import base64
import json

import pytest
from nzshm_common.util import compress_string, decompress_string

from graphql_api.data import dynamo
from graphql_api.schema import schema

CREATE_AT_MUTATION = """
mutation CreateTask($input: CreateAutomationTaskInput!) {
    create_automation_task(input: $input) {
        task_result { id }
    }
}
"""

CREATE_FILE_MUTATION = """
mutation CreateFile($file_name: String!, $md5_digest: String!, $file_size: BigInt!, $created: DateTime = null, $meta: [KeyValuePairInput!] = null) {
    create_file(file_name: $file_name, md5_digest: $md5_digest, file_size: $file_size, created: $created, meta: $meta) {
        ok
        file_result { id file_name }
    }
}
"""

CREATE_FILE_RELATION_MUTATION = """
mutation CreateFileRelation($file_id: ID!, $role: FileRole!, $thing_id: ID!) {
    create_file_relation(file_id: $file_id, role: $role, thing_id: $thing_id) { ok }
}
"""

FILE_WITH_RELATIONS_QUERY = """
query GetFile($id: ID!) {
    node(id: $id) {
        ... on File {
            id
            file_name
            relations {
                total_count
                edges {
                    node {
                        role
                        thing {
                            ... on AutomationTask { id }
                            ... on GeneralTask { id }
                            ... on RuptureGenerationTask { id }
                        }
                    }
                }
            }
        }
    }
}
"""


@pytest.fixture
def lower_threshold(monkeypatch):
    """Drop UNCOMPRESSED_LIMIT to 25 so threshold-crossing tests run fast."""
    monkeypatch.setattr(dynamo, "UNCOMPRESSED_LIMIT", 25)
    return 25


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_helper_round_trip():
    """_ensure_decompressed accepts both list and compressed-string forms."""
    relations = [{"id": f"100000abc{i:03d}", "role": "read"} for i in range(150)]
    compressed = compress_string(json.dumps(relations))
    assert isinstance(compressed, str)

    assert dynamo._ensure_decompressed(relations) == relations
    assert dynamo._ensure_decompressed(compressed) == relations
    assert dynamo._ensure_decompressed(None) == []


def test_relations_stored_as_list_under_threshold(gql_context, lower_threshold):
    """At <UNCOMPRESSED_LIMIT relations, storage stays as a JSON list."""
    file_result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "file_name": "compression_under.zip",
            "md5_digest": "00aa",
            "file_size": 1024,
            "created": "2024-07-01T00:00:00Z",
        },
        context_value=gql_context,
    )
    assert file_result.errors is None, file_result.errors
    file_gid = file_result.data["create_file"]["file_result"]["id"]
    file_raw_id = base64.b64decode(file_gid).decode().split(":")[1]

    # Add 5 relations — well below the lowered threshold of 25.
    for _i in range(5):
        at = schema.execute_sync(
            CREATE_AT_MUTATION,
            variable_values={
                "input": {
                    "state": "DONE",
                    "result": "SUCCESS",
                    "task_type": "INVERSION",
                    "created": "2024-07-01T00:00:00Z",
                }
            },
            context_value=gql_context,
        )
        assert at.errors is None, at.errors
        thing_gid = at.data["create_automation_task"]["task_result"]["id"]
        rel = schema.execute_sync(
            CREATE_FILE_RELATION_MUTATION,
            variable_values={"thing_id": thing_gid, "file_id": file_gid, "role": "READ"},
            context_value=gql_context,
        )
        assert rel.errors is None, rel.errors

    raw = gql_context["dynamodb"].Table("ToshiFileObject-TEST").get_item(Key={"object_id": file_raw_id})["Item"]
    stored = json.loads(raw["object_content"])
    assert isinstance(stored["relations"], list)
    assert len(stored["relations"]) == 5


def test_relations_compressed_above_threshold(gql_context, lower_threshold):
    """Crossing UNCOMPRESSED_LIMIT switches storage to compressed-string form."""
    file_result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "file_name": "compression_over.zip",
            "md5_digest": "01bb",
            "file_size": 1024,
            "created": "2024-07-02T00:00:00Z",
        },
        context_value=gql_context,
    )
    assert file_result.errors is None, file_result.errors
    file_gid = file_result.data["create_file"]["file_result"]["id"]
    file_raw_id = base64.b64decode(file_gid).decode().split(":")[1]

    # Add lower_threshold + 1 = 26 relations to cross the threshold.
    for _i in range(lower_threshold + 1):
        at = schema.execute_sync(
            CREATE_AT_MUTATION,
            variable_values={
                "input": {
                    "state": "DONE",
                    "result": "SUCCESS",
                    "task_type": "INVERSION",
                    "created": "2024-07-02T00:00:00Z",
                }
            },
            context_value=gql_context,
        )
        assert at.errors is None, at.errors
        thing_gid = at.data["create_automation_task"]["task_result"]["id"]
        rel = schema.execute_sync(
            CREATE_FILE_RELATION_MUTATION,
            variable_values={"thing_id": thing_gid, "file_id": file_gid, "role": "READ"},
            context_value=gql_context,
        )
        assert rel.errors is None, rel.errors

    raw = gql_context["dynamodb"].Table("ToshiFileObject-TEST").get_item(Key={"object_id": file_raw_id})["Item"]
    stored = json.loads(raw["object_content"])
    assert isinstance(stored["relations"], str), (
        f"expected compressed-string storage above threshold, got {type(stored['relations']).__name__}"
    )
    # The compressed payload round-trips back to the full list.
    decompressed = json.loads(decompress_string(stored["relations"]))
    assert len(decompressed) == lower_threshold + 1


def test_relations_round_trip_through_graphql(gql_context, lower_threshold):
    """Query node(id:) on a file with compressed relations returns full count + edges."""
    file_result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "file_name": "compression_roundtrip.zip",
            "md5_digest": "02cc",
            "file_size": 1024,
            "created": "2024-07-03T00:00:00Z",
        },
        context_value=gql_context,
    )
    assert file_result.errors is None, file_result.errors
    file_gid = file_result.data["create_file"]["file_result"]["id"]

    thing_gids = []
    for _i in range(lower_threshold + 5):  # 30 relations, well above threshold
        at = schema.execute_sync(
            CREATE_AT_MUTATION,
            variable_values={
                "input": {
                    "state": "DONE",
                    "result": "SUCCESS",
                    "task_type": "INVERSION",
                    "created": "2024-07-03T00:00:00Z",
                }
            },
            context_value=gql_context,
        )
        assert at.errors is None, at.errors
        thing_gid = at.data["create_automation_task"]["task_result"]["id"]
        thing_gids.append(thing_gid)
        rel = schema.execute_sync(
            CREATE_FILE_RELATION_MUTATION,
            variable_values={"thing_id": thing_gid, "file_id": file_gid, "role": "READ"},
            context_value=gql_context,
        )
        assert rel.errors is None, rel.errors

    # Query the file — node lookup should decompress transparently.
    result = schema.execute_sync(FILE_WITH_RELATIONS_QUERY, variable_values={"id": file_gid}, context_value=gql_context)
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["file_name"] == "compression_roundtrip.zip"
    assert node["relations"]["total_count"] == lower_threshold + 5

    returned_thing_ids = {edge["node"]["thing"]["id"] for edge in node["relations"]["edges"]}
    assert returned_thing_ids == set(thing_gids)


def test_pre_compressed_legacy_data_reads_correctly(gql_context):
    """A pre-existing file with relations already stored as a compressed string
    (e.g. read from legacy production DynamoDB) must round-trip through node lookup."""
    file_result = schema.execute_sync(
        CREATE_FILE_MUTATION,
        variable_values={
            "file_name": "legacy_compressed.zip",
            "md5_digest": "03dd",
            "file_size": 1024,
            "created": "2024-07-04T00:00:00Z",
        },
        context_value=gql_context,
    )
    assert file_result.errors is None, file_result.errors
    file_gid = file_result.data["create_file"]["file_result"]["id"]
    file_raw_id = base64.b64decode(file_gid).decode().split(":")[1]

    # Directly write a compressed-string relations field — bypassing the mutation
    # so we exercise the read-side decompression in isolation.
    table = gql_context["dynamodb"].Table("ToshiFileObject-TEST")
    item = table.get_item(Key={"object_id": file_raw_id})["Item"]
    content = json.loads(item["object_content"])
    fake_relations = [{"id": f"10000{i:03d}xyz", "role": "read"} for i in range(60)]
    content["relations"] = compress_string(json.dumps(fake_relations))
    table.put_item(
        Item={
            "object_id": file_raw_id,
            "object_type": item["object_type"],
            "object_content": json.dumps(content),
        }
    )

    # Read it back via the standard get_file path used by node lookup.
    data = dynamo.get_file(gql_context["dynamodb"], file_raw_id)
    assert isinstance(data["relations"], list), (
        f"get_file must decompress legacy compressed-string rows; got {type(data['relations']).__name__}"
    )
    assert len(data["relations"]) == 60


def test_80k_relations_fit_under_dynamodb_limit():
    """Ceiling check: legacy depends on 80k relations compressing under 390KB.
    This guards against any future change to compress_string semantics (e.g.
    swapping compression algo) that would silently shrink the headroom."""
    relations = [{"id": f"{100_000 + i:09d}", "role": "read"} for i in range(80_000)]
    compressed = compress_string(json.dumps(relations))
    assert len(compressed) < 390_000, (
        f"compressed 80k relations = {len(compressed)} bytes; expected <390KB to "
        f"stay under DynamoDB's 400KB item-size limit"
    )
