"""Regression tests for COVERAGE_GAPS.md Gap 4 — RuptureSet mutation validation + upload.

Ports two legacy test files:

  - graphql_api/tests/rupture_set/test_rupture_set_mutation_checks.py
    Input field validation: missing required attributes, invalid `created`,
    invalid `fault_models` shape.

  - graphql_api/tests/rupture_set/test_rupture_set_upload.py
    The full presigned-POST upload flow: client generates a RuptureSet,
    receives `post_url` / `post_url_v2` / `post_data_v2`, then uploads
    the actual file bytes via the presigned POST.

The POC was missing both:
  - `CreateRuptureSetInput` declared `md5_digest` and `file_size` as
    nullable, diverging from legacy's `String!` / `BigInt!` and silently
    allowing malformed records;
  - `FileInterface.post_url*` returned `None` unconditionally — no S3
    presigned-POST generation at create time.

This file pins the closures: input validation matches legacy SDL, and
the upload round-trip works end-to-end against moto-mocked S3.
"""

import base64
import datetime as dt
import hashlib
import io
import json

import boto3
import pytest
import requests
from moto import mock_aws

from graphql_api.schema import schema

_BUCKET = "toshi-strawberry-test"


@pytest.fixture
def s3_bucket(monkeypatch):
    """moto-backed S3 bucket; patches data.s3 module-level constants so
    `boto3.client("s3", ...)` calls inside `presigned_post_for_file` resolve
    against the mock. See issue #312 concern 3 for the underlying
    env-var-caching issue this works around.
    """
    import graphql_api.data.s3 as s3_mod  # noqa: PLC0415

    monkeypatch.setattr(s3_mod, "S3_BUCKET_NAME", _BUCKET)
    with mock_aws():
        client = boto3.client("s3", region_name=s3_mod.REGION)
        # Non-us-east-1 buckets require LocationConstraint.
        client.create_bucket(
            Bucket=_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": s3_mod.REGION},
        )
        yield client


@pytest.fixture
def rupture_gen_task_id(gql_context):
    from graphql_api.data.dynamo import create_thing  # noqa: PLC0415

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2026-01-01T00:00:00Z"},
    )
    raw = data["object_id"]
    return base64.b64encode(f"RuptureGenerationTask:{raw}".encode()).decode()


# ── 1. Required-field validation (mutation_checks.py port) ────────────────────


def test_create_rupture_set_missing_required_fields_fails(gql_context, rupture_gen_task_id):
    """Mirrors test_create_rupture_set_with_missing_file_attributes_fails.

    Legacy SDL: `file_name: String!`, `md5_digest: String!`, `file_size: BigInt!`,
    `produced_by: ID!`. Sending an empty input must fail GraphQL validation
    before reaching the resolver.
    """
    query = """
    mutation {
        create_rupture_set(input: { created: "2022-03-03T00:17:52.352274+00:00" }) {
            rupture_set { id }
        }
    }
    """
    result = schema.execute_sync(query, context_value=gql_context)
    assert result.errors is not None
    messages = " ".join(str(e) for e in result.errors)
    # GraphQL surfaces all missing-required-field errors in one validation pass.
    for field in ("file_name", "md5_digest", "file_size", "produced_by"):
        assert field in messages, f"expected missing-field error for {field}, got: {messages}"


def test_create_rupture_set_with_valid_created(gql_context, rupture_gen_task_id):
    """Mirrors the happy-path branch of test_create_rupture_set_valid_created.

    The legacy test also exercised invalid `created` values (empty string,
    arbitrary strings, integers) and expected Graphene's DateTime scalar to
    reject them. The POC's DateTime scalar is intentionally permissive
    (`parse_value=str`, see ADR-001 Phase 1) — tightening it is tracked
    separately and is out of scope for Gap 4. Wire-compat for the
    happy-path is what RuptureSet creation actually depends on.
    """
    mutation = """
    mutation CreateRS($input: CreateRuptureSetInput!) {
        create_rupture_set(input: $input) {
            rupture_set { id file_name created }
        }
    }
    """
    variables = {
        "input": {
            "file_name": "file_name",
            "md5_digest": "digest",
            "file_size": 1000,
            "produced_by": rupture_gen_task_id,
            "created": dt.datetime.now(dt.UTC).isoformat(),
            "fault_models": ["A", "B"],
            "metrics": [{"k": "some_metric", "v": "20"}],
        }
    }
    result = schema.execute_sync(mutation, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    assert result.data["create_rupture_set"]["rupture_set"]["file_name"] == "file_name"


def test_create_rupture_set_fault_models_list_of_strings(gql_context, rupture_gen_task_id):
    """Mirrors the happy-path branch of test_create_rupture_set_valid_fault_models."""
    mutation = """
    mutation CreateRS($input: CreateRuptureSetInput!) {
        create_rupture_set(input: $input) {
            rupture_set { id fault_models }
        }
    }
    """
    variables = {
        "input": {
            "file_name": "file_name",
            "md5_digest": "digest",
            "file_size": 1000,
            "produced_by": rupture_gen_task_id,
            "created": "2026-01-01T00:00:00Z",
            "fault_models": ["ModelA", "ModelB"],
        }
    }
    result = schema.execute_sync(mutation, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    assert result.data["create_rupture_set"]["rupture_set"]["fault_models"] == ["ModelA", "ModelB"]


def test_create_rupture_set_fault_models_rejects_scalar(gql_context, rupture_gen_task_id):
    """Mirrors the integer-rejection branch of test_create_rupture_set_valid_fault_models.

    `fault_models: [String]` requires a list. Passing a scalar 1001 must fail
    at the GraphQL input-coercion layer.
    """
    mutation = """
    mutation CreateRS($input: CreateRuptureSetInput!) {
        create_rupture_set(input: $input) {
            rupture_set { id }
        }
    }
    """
    variables = {
        "input": {
            "file_name": "file_name",
            "md5_digest": "digest",
            "file_size": 1000,
            "produced_by": rupture_gen_task_id,
            "created": "2026-01-01T00:00:00Z",
            "fault_models": 1001,
        }
    }
    result = schema.execute_sync(mutation, variable_values=variables, context_value=gql_context)
    assert result.errors is not None
    assert any("fault_models" in str(e) for e in result.errors)


# ── 2. Presigned-POST upload round-trip (upload.py port) ──────────────────────


CREATE_RS_WITH_POST_URLS = """
mutation CreateRS($input: CreateRuptureSetInput!) {
    create_rupture_set(input: $input) {
        rupture_set {
            id
            file_name
            md5_digest
            post_url
            post_url_v2
            post_data_v2
        }
    }
}
"""


def test_create_rupture_set_post_url_fields_populated(gql_context, rupture_gen_task_id, s3_bucket):
    """create_rupture_set generates a presigned-POST and surfaces it on the
    immediate response — matches the post_url / post_url_v2 / post_data_v2
    contract that nzshm-toshi-client and runzi consume.

    Without S3 configured, all three would return null (FileInterface default).
    Mocking S3 via moto and patching `data.s3.S3_BUCKET_NAME` exercises the
    real codepath.
    """
    variables = {
        "input": {
            "file_name": "rupture.zip",
            "md5_digest": "abc==",
            "file_size": 1024,
            "produced_by": rupture_gen_task_id,
            "created": "2026-01-01T00:00:00Z",
            "fault_models": ["ModelA"],
        }
    }
    result = schema.execute_sync(CREATE_RS_WITH_POST_URLS, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    rs = result.data["create_rupture_set"]["rupture_set"]

    assert rs["post_url"], "post_url must be populated when S3 is configured"
    assert rs["post_url_v2"], "post_url_v2 must be populated when S3 is configured"
    assert rs["post_data_v2"], "post_data_v2 must be populated when S3 is configured"

    # Legacy invariant: post_url and post_data_v2 are both json.dumps(fields).
    assert json.loads(rs["post_url"]) == json.loads(rs["post_data_v2"])
    fields = json.loads(rs["post_url"])
    assert fields.get("Content-MD5") == "abc=="
    assert "key" in fields, "presigned-POST fields must include the S3 key"


def test_create_rupture_set_and_upload_via_requests(gql_context, rupture_gen_task_id, s3_bucket):
    """Ports test_create_rupture_set_and_upload_file_using_method (upload_option=1).

    Full round-trip: create RS → receive presigned POST → upload file content
    via `requests.post` → verify the bytes landed at the expected S3 key.
    """
    file_name = "a_line_or_two.txt"
    file_content = b"a line\nor two\n"
    digest = hashlib.sha256(file_content).hexdigest()

    variables = {
        "input": {
            "file_name": file_name,
            "md5_digest": digest,
            "file_size": len(file_content),
            "produced_by": rupture_gen_task_id,
            "created": "2026-01-01T00:00:00Z",
            "fault_models": ["ModelA", "ModelB"],
        }
    }
    result = schema.execute_sync(CREATE_RS_WITH_POST_URLS, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    rs = result.data["create_rupture_set"]["rupture_set"]

    url = rs["post_url_v2"]
    fields = json.loads(rs["post_data_v2"])
    response = requests.post(url, data=fields, files={"file": io.BytesIO(file_content)}, timeout=5)
    assert response.status_code == 204, f"S3 POST returned {response.status_code}: {response.text}"

    # Verify the bytes landed.
    s3 = s3_bucket
    obj = s3.get_object(Bucket=_BUCKET, Key=fields["key"])
    assert obj["Body"].read() == file_content


def test_post_url_null_without_s3(gql_context, rupture_gen_task_id, monkeypatch):
    """When S3 is not configured (default), post_url* must be null —
    matches the FileInterface default and keeps the schema honest.
    """
    import graphql_api.data.s3 as s3_mod  # noqa: PLC0415

    monkeypatch.setattr(s3_mod, "S3_BUCKET_NAME", "")

    variables = {
        "input": {
            "file_name": "rs.zip",
            "md5_digest": "x",
            "file_size": 1,
            "produced_by": rupture_gen_task_id,
            "created": "2026-01-01T00:00:00Z",
            "fault_models": ["A"],
        }
    }
    result = schema.execute_sync(CREATE_RS_WITH_POST_URLS, variable_values=variables, context_value=gql_context)
    assert result.errors is None, result.errors
    rs = result.data["create_rupture_set"]["rupture_set"]
    assert rs["post_url"] is None
    assert rs["post_url_v2"] is None
    assert rs["post_data_v2"] is None
