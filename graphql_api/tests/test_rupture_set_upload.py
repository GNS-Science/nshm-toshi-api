"""
Tests for RuptureSet upload URL fields (post_url, post_url_v2, file_url).

Covers COVERAGE_GAPS.md gap 9 — guards the schema-level contract that
weka relies on for upload/download URL generation. In the POC, these
resolvers are stubs returning None (S3 is not exercised); the tests
confirm the fields are queryable without error and have the correct
nullable String types.
"""

import pytest

from graphql_api.schema import schema

CREATE_RS_MUTATION = """
mutation($input: CreateRuptureSetInput!) {
    create_rupture_set(input: $input) {
        ok
        rupture_set {
            id
            file_name
            file_url
            post_url
            post_url_v2
            post_data_v2
        }
    }
}
"""

NODE_QUERY = """
query GetNode($id: ID!) {
    node(id: $id) {
        id
        ... on RuptureSet {
            file_name
            file_url
            post_url
            post_url_v2
            post_data_v2
        }
    }
}
"""


@pytest.fixture(scope="module")
def rgt_id(gql_context):
    import base64

    from graphql_api.data.dynamo import create_thing

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2024-01-01T00:00:00Z"},
    )
    return base64.b64encode(f"RuptureGenerationTask:{data['object_id']}".encode()).decode()


@pytest.fixture(scope="module")
def created_rupture_set(gql_context, rgt_id):
    result = schema.execute_sync(
        CREATE_RS_MUTATION,
        variable_values={
            "input": {
                "file_name": "upload_test.zip",
                "produced_by": rgt_id,
                "md5_digest": "feedface",
                "file_size": 1_048_576,
                "created": "2024-04-01T00:00:00Z",
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    return result.data["create_rupture_set"]["rupture_set"]


def test_post_url_fields_queryable_on_create(created_rupture_set):
    """All upload URL fields resolve without error on the create payload."""
    rs = created_rupture_set
    assert rs["file_name"] == "upload_test.zip"
    # In POC: stubs return null; the schema-level contract is what's tested
    assert rs["post_url"] is None
    assert rs["post_url_v2"] is None
    assert rs["post_data_v2"] is None


def test_file_url_resolves_without_error(created_rupture_set):
    """file_url calls presigned_download_url; returns None when S3 not configured."""
    rs = created_rupture_set
    assert "file_url" in rs


def test_post_url_fields_queryable_via_node(gql_context, created_rupture_set):
    """Same upload URL fields resolve via the node(id:) query."""
    result = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created_rupture_set["id"]}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    node = result.data["node"]
    assert node["file_name"] == "upload_test.zip"
    assert node["post_url"] is None
    assert node["post_url_v2"] is None
    assert node["post_data_v2"] is None


def test_file_url_uses_presigned_download_url(gql_context, created_rupture_set, monkeypatch):
    """file_url must delegate to presigned_download_url with (pk, file_name)."""
    from graphql_api.models import file_interface as fi

    captured = {}

    def fake_presigner(object_id, file_name):
        captured["object_id"] = object_id
        captured["file_name"] = file_name
        return f"https://fake-bucket.s3/{object_id}/{file_name}"

    monkeypatch.setattr(fi, "presigned_download_url", fake_presigner)

    result = schema.execute_sync(
        NODE_QUERY, variable_values={"id": created_rupture_set["id"]}, context_value=gql_context
    )
    assert result.errors is None, result.errors
    assert result.data["node"]["file_url"] == f"https://fake-bucket.s3/{captured['object_id']}/upload_test.zip"
    assert captured["file_name"] == "upload_test.zip"
