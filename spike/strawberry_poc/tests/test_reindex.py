"""
Tests for the reindex mutation.

reindex(id_in: [ID!]!) re-pushes each object to Elasticsearch by:
  1. Decoding the relay global ID → (type_name, raw_id)
  2. Fetching the current object from DynamoDB
  3. Calling index_document with the correct ThingData_/FileData_ key prefix

Unit tests mock index_document so no live ES is required.
Integration test verifies the document actually lands in ES.
"""

from unittest.mock import patch

import pytest

from schema import schema

CREATE_GT = """
mutation { create_general_task(input: { title: "Reindex Me", created: "2024-01-01T00:00Z" }) {
    general_task { id }
} }
"""

CREATE_FILE = """
mutation { create_file(file_name: "reindex.txt", file_size: 1, md5_digest: "abc") {
    file_result { id }
} }
"""

REINDEX_MUTATION = """
mutation Reindex($ids: [ID!]!) {
    reindex(id_in: $ids) {
        ok
        reindexed_ids
    }
}
"""


def run(query, gql_context, variables=None):
    result = schema.execute_sync(query, context_value=gql_context, variable_values=variables or {})
    assert result.errors is None, result.errors
    return result.data


# ── Unit tests (no ES required) ───────────────────────────────────────────────


def test_reindex_thing_calls_index_document(gql_context):
    """reindex on a GeneralTask calls index_document with ThingData_ prefix."""
    gt_id = run(CREATE_GT, gql_context)["create_general_task"]["general_task"]["id"]

    with patch("data.search.index_document") as mock_index:
        result = run(REINDEX_MUTATION, gql_context, {"ids": [gt_id]})

    assert result["reindex"]["ok"] is True
    assert gt_id in result["reindex"]["reindexed_ids"]
    assert mock_index.called
    key = mock_index.call_args[0][0]
    assert key.startswith("ThingData_")


def test_reindex_file_calls_index_document(gql_context):
    """reindex on a ToshiFile calls index_document with FileData_ prefix."""
    file_id = run(CREATE_FILE, gql_context)["create_file"]["file_result"]["id"]

    with patch("data.search.index_document") as mock_index:
        result = run(REINDEX_MUTATION, gql_context, {"ids": [file_id]})

    assert result["reindex"]["ok"] is True
    assert file_id in result["reindex"]["reindexed_ids"]
    key = mock_index.call_args[0][0]
    assert key.startswith("FileData_")


def test_reindex_multiple_ids(gql_context):
    """reindex accepts a batch of IDs and returns all of them."""
    gt_id = run(CREATE_GT, gql_context)["create_general_task"]["general_task"]["id"]
    file_id = run(CREATE_FILE, gql_context)["create_file"]["file_result"]["id"]

    with patch("data.search.index_document"):
        result = run(REINDEX_MUTATION, gql_context, {"ids": [gt_id, file_id]})

    assert result["reindex"]["ok"] is True
    assert set(result["reindex"]["reindexed_ids"]) == {gt_id, file_id}


def test_reindex_unknown_id_skipped(gql_context):
    """An ID that doesn't exist in DynamoDB is silently skipped."""
    from strawberry.relay import GlobalID

    fake_id = str(GlobalID("GeneralTask", "999999zzzzz"))

    with patch("data.search.index_document") as mock_index:
        result = run(REINDEX_MUTATION, gql_context, {"ids": [fake_id]})

    assert result["reindex"]["ok"] is True
    assert result["reindex"]["reindexed_ids"] == []
    mock_index.assert_not_called()


def test_reindex_empty_list(gql_context):
    """Empty id_in returns ok with empty reindexed_ids."""
    result = run(REINDEX_MUTATION, gql_context, {"ids": []})
    assert result["reindex"]["ok"] is True
    assert result["reindex"]["reindexed_ids"] == []


# ── Integration test — requires live ES ──────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(not __import__("os").environ.get("ES_ENDPOINT"), reason="requires ES_ENDPOINT")
def test_reindex_document_lands_in_es(gql_context):
    """After reindex, the document is queryable from ES."""
    import time

    import requests as _req

    gt_id = run(CREATE_GT, gql_context)["create_general_task"]["general_task"]["id"]
    ep = gql_context.get("es_endpoint", "")
    idx = gql_context.get("es_index", "toshi-index-mapped")

    # Delete and re-index to confirm reindex actually writes
    from strawberry.relay import GlobalID

    gid = GlobalID.from_id(gt_id)
    key = f"ThingData_{gid.node_id}"
    _req.delete(f"{ep}/{idx}/_doc/{key}", timeout=5)
    time.sleep(0.5)

    result = run(REINDEX_MUTATION, gql_context, {"ids": [gt_id]})
    assert result["reindex"]["ok"] is True
    time.sleep(1)

    resp = _req.get(f"{ep}/{idx}/_doc/{key}", timeout=5).json()
    assert resp.get("found") is True
    assert resp["_source"]["clazz_name"] == "GeneralTask"
