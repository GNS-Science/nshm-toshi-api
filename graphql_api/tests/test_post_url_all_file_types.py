"""Regression tests — `post_url` must be populated on every file-create mutation.

The Gap 4 closure in PR #310 wired `presigned_post_for_file` into
`mutate_create_rupture_set` only. Every other file-create mutation still
returned `null` for `post_url`, breaking nshm-toshi-client/runzi which
unconditionally `json.loads(post_url)` after each create call.

These tests lock in the contract for the remaining six file types so a
future refactor can't quietly drop the presigned-POST again:

  - create_file                       (plain File / ToshiFile)
  - create_inversion_solution
  - create_scaled_inversion_solution
  - create_aggregate_inversion_solution
  - create_time_dependent_inversion_solution
  - create_inversion_solution_nrml

For each: confirm `post_url` is a JSON string of field values that round-
trips through `json.loads`. Doesn't repeat the full requests-based upload
round-trip — that's already covered by test_bugfix_gap4_rupture_set.py
and the codepath is identical.
"""

import base64
import json

import boto3
import pytest
from moto import mock_aws

from graphql_api.schema import schema

_BUCKET = "toshi-strawberry-test-allfiles"


@pytest.fixture
def s3_bucket(monkeypatch):
    """moto-backed S3 bucket; matches the pattern in test_bugfix_gap4_rupture_set."""
    import graphql_api.data.s3 as s3_mod  # noqa: PLC0415

    monkeypatch.setattr(s3_mod, "S3_BUCKET_NAME", _BUCKET)
    with mock_aws():
        client = boto3.client("s3", region_name=s3_mod.REGION)
        client.create_bucket(
            Bucket=_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": s3_mod.REGION},
        )
        yield client


@pytest.fixture
def rgt_id(gql_context):
    from graphql_api.data.dynamo import create_thing  # noqa: PLC0415

    data = create_thing(
        gql_context["dynamodb"],
        "RuptureGenerationTask",
        {"state": "done", "result": "success", "created": "2026-01-01T00:00:00Z"},
    )
    raw = data["object_id"]
    return base64.b64encode(f"RuptureGenerationTask:{raw}".encode()).decode()


@pytest.fixture
def at_id(gql_context):
    from graphql_api.data.dynamo import create_thing  # noqa: PLC0415

    data = create_thing(
        gql_context["dynamodb"],
        "AutomationTask",
        {"state": "done", "result": "success", "task_type": "INVERSION", "created": "2026-01-01T00:00:00Z"},
    )
    raw = data["object_id"]
    return base64.b64encode(f"AutomationTask:{raw}".encode()).decode()


def _create(mutation: str, variables: dict, gql_context):
    return schema.execute_sync(mutation, variable_values=variables, context_value=gql_context)


def _assert_post_url_is_valid_json(payload: dict, file_node_key: str):
    """Every file create response in legacy/POC returns a `post_url` that
    nshm-toshi-client immediately `json.loads`. Confirm the contract."""
    post_url = payload[file_node_key]["post_url"]
    assert post_url, f"post_url is null/empty on {file_node_key} — runzi will crash on json.loads"
    parsed = json.loads(post_url)
    assert isinstance(parsed, dict), f"post_url did not deserialize to a dict on {file_node_key}: {parsed!r}"
    # The presigned-POST fields dict from boto3 always contains `key`.
    assert "key" in parsed, f"post_url fields missing `key` on {file_node_key}"


# ── 1. Plain File / ToshiFile ─────────────────────────────────────────────────


def test_create_file_post_url(gql_context, s3_bucket):
    mutation = """
    mutation CreateFile($file_name: String!, $md5_digest: String!, $file_size: BigInt!, $created: DateTime = null, $meta: [KeyValuePairInput!] = null) {
        create_file(file_name: $file_name, md5_digest: $md5_digest, file_size: $file_size, created: $created, meta: $meta) {
            ok
            file_result { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {"file_name": "f.zip", "md5_digest": "abc==", "file_size": 100},
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_file"], "file_result")


# ── 2. InversionSolution ──────────────────────────────────────────────────────


def test_create_inversion_solution_post_url(gql_context, s3_bucket, at_id):
    mutation = """
    mutation CreateIS($input: CreateInversionSolutionInput!) {
        create_inversion_solution(input: $input) {
            ok
            inversion_solution { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {
            "input": {
                "file_name": "is.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_inversion_solution"], "inversion_solution")


# ── 3. ScaledInversionSolution ────────────────────────────────────────────────


def test_create_scaled_inversion_solution_post_url(gql_context, s3_bucket, at_id):
    # Need a source IS first.
    create_is = """
    mutation CreateIS($input: CreateInversionSolutionInput!) {
        create_inversion_solution(input: $input) {
            inversion_solution { id }
        }
    }
    """
    is_res = _create(
        create_is,
        {
            "input": {
                "file_name": "is.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert is_res.errors is None, is_res.errors
    source_id = is_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    mutation = """
    mutation CreateSIS($input: CreateScaledInversionSolutionInput!) {
        create_scaled_inversion_solution(input: $input) {
            ok
            solution { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {
            "input": {
                "file_name": "sis.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "source_solution": source_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_scaled_inversion_solution"], "solution")


# ── 4. AggregateInversionSolution ─────────────────────────────────────────────


def test_create_aggregate_inversion_solution_post_url(gql_context, s3_bucket, at_id, rgt_id):
    # Need a RuptureSet (common_rupture_set) and at least one source IS.
    create_rs = """
    mutation CreateRS($input: CreateRuptureSetInput!) {
        create_rupture_set(input: $input) { rupture_set { id } }
    }
    """
    rs_res = _create(
        create_rs,
        {
            "input": {
                "file_name": "rs.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": rgt_id,
                "created": "2026-01-01T00:00:00Z",
                "fault_models": ["A"],
            }
        },
        gql_context,
    )
    assert rs_res.errors is None, rs_res.errors
    rs_id = rs_res.data["create_rupture_set"]["rupture_set"]["id"]

    create_is = """
    mutation CreateIS($input: CreateInversionSolutionInput!) {
        create_inversion_solution(input: $input) { inversion_solution { id } }
    }
    """
    is_res = _create(
        create_is,
        {
            "input": {
                "file_name": "is.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    is_id = is_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    mutation = """
    mutation CreateAIS($input: CreateAggregateInversionSolutionInput!) {
        create_aggregate_inversion_solution(input: $input) {
            ok
            solution { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {
            "input": {
                "file_name": "ais.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "common_rupture_set": rs_id,
                "source_solutions": [is_id],
                "aggregation_fn": "MEAN",
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_aggregate_inversion_solution"], "solution")


# ── 5. TimeDependentInversionSolution ─────────────────────────────────────────


def test_create_time_dependent_inversion_solution_post_url(gql_context, s3_bucket, at_id):
    create_is = """
    mutation CreateIS($input: CreateInversionSolutionInput!) {
        create_inversion_solution(input: $input) { inversion_solution { id } }
    }
    """
    is_res = _create(
        create_is,
        {
            "input": {
                "file_name": "is.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    source_id = is_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    mutation = """
    mutation CreateTDIS($input: CreateTimeDependentInversionSolutionInput!) {
        create_time_dependent_inversion_solution(input: $input) {
            ok
            solution { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {
            "input": {
                "file_name": "tdis.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "source_solution": source_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_time_dependent_inversion_solution"], "solution")


# ── 6. InversionSolutionNrml ──────────────────────────────────────────────────


def test_create_inversion_solution_nrml_post_url(gql_context, s3_bucket, at_id):
    create_is = """
    mutation CreateIS($input: CreateInversionSolutionInput!) {
        create_inversion_solution(input: $input) { inversion_solution { id } }
    }
    """
    is_res = _create(
        create_is,
        {
            "input": {
                "file_name": "is.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    source_id = is_res.data["create_inversion_solution"]["inversion_solution"]["id"]

    mutation = """
    mutation CreateNRML($input: CreateInversionSolutionNrmlInput!) {
        create_inversion_solution_nrml(input: $input) {
            ok
            inversion_solution_nrml { id post_url }
        }
    }
    """
    result = _create(
        mutation,
        {
            "input": {
                "file_name": "nrml.zip",
                "md5_digest": "abc==",
                "file_size": 100,
                "source_solution": source_id,
                "created": "2026-01-01T00:00:00Z",
            }
        },
        gql_context,
    )
    assert result.errors is None, result.errors
    _assert_post_url_is_valid_json(result.data["create_inversion_solution_nrml"], "inversion_solution_nrml")
