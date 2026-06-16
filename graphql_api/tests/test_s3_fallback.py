"""
Tests for S3 fallback on legacy objects (pre-DynamoDB-migration data).

The legacy production API stored objects in S3 before ~2022 and progressively
migrated them to DynamoDB. Objects with IDs below FIRST_DYNAMO_ID (100000)
still live only in S3. Reads must fall back to S3 when DynamoDB misses;
otherwise pre-2022 objects look like "not found" / "Unexpected error".

Covers COVERAGE_GAPS.md gap 7 (S3 fallback and DynamoDB+S3 mixed queries).
Mirrors graphql_api/tests/test_s3_fallback.py + test_dynamo_and_s3_queries.py.

These tests use moto rather than the testcontainers DDB fixture so the S3
mock and DDB mock share one mocked-AWS context.
"""

import json

import boto3
import pytest
from moto import mock_aws

BUCKET = "test-toshi-poc-s3-fallback"
STAGE = "TEST"
REGION = "us-east-1"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def s3_env(monkeypatch):
    """Point both data modules at our mocked bucket and reset module-level constants."""
    from data import dynamo as dynamo_mod
    from data import s3 as s3_mod

    monkeypatch.setattr(dynamo_mod, "S3_BUCKET_NAME", BUCKET)
    monkeypatch.setattr(s3_mod, "S3_BUCKET_NAME", BUCKET)
    monkeypatch.setattr(s3_mod, "REGION", REGION)
    yield BUCKET


@pytest.fixture
def mocked_aws(s3_env):
    """Bring up moto S3 + DynamoDB and create the bucket + tables."""
    with mock_aws():
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(Bucket=BUCKET)

        ddb = boto3.resource("dynamodb", region_name=REGION)
        for table_name in (
            f"ToshiThingObject-{STAGE}",
            f"ToshiFileObject-{STAGE}",
            f"ToshiTableObject-{STAGE}",
        ):
            ddb.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": "object_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "object_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )

        yield {"s3": s3, "dynamodb": ddb}


def _put_s3_object(s3, key: str, body: dict) -> None:
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(body))


# ── _from_s3 helper unit tests ────────────────────────────────────────────────


def test_from_s3_returns_none_when_bucket_unset(monkeypatch):
    """_from_s3 short-circuits when S3_BUCKET_NAME is empty."""
    from data import dynamo as dynamo_mod

    monkeypatch.setattr(dynamo_mod, "S3_BUCKET_NAME", "")
    assert dynamo_mod._from_s3("12345", "ThingData") is None


def test_from_s3_returns_none_on_miss(mocked_aws):
    """Object that doesn't exist in S3 returns None, not an exception."""
    from data import dynamo as dynamo_mod

    assert dynamo_mod._from_s3("does-not-exist", "ThingData") is None


def test_from_s3_returns_parsed_dict_on_hit(mocked_aws):
    """Object stored at the expected key path returns the parsed JSON."""
    from data import dynamo as dynamo_mod

    body = {
        "object_id": "12345",
        "clazz_name": "RuptureGenerationTask",
        "created": "2021-06-01T00:00:00Z",
        "state": "done",
    }
    _put_s3_object(mocked_aws["s3"], "ThingData/12345/object.json", body)

    result = dynamo_mod._from_s3("12345", "ThingData")
    assert result == body


# ── get_thing / get_file / get_table S3 fallback ──────────────────────────────


def test_get_thing_falls_back_to_s3(mocked_aws):
    """DynamoDB miss → returns S3 data with object_id populated."""
    from data import dynamo as dynamo_mod

    body = {"clazz_name": "GeneralTask", "title": "legacy GT", "created": "2021-05-01T00:00:00Z"}
    _put_s3_object(mocked_aws["s3"], "ThingData/567/object.json", body)

    result = dynamo_mod.get_thing(mocked_aws["dynamodb"], "567")
    assert result is not None
    assert result["clazz_name"] == "GeneralTask"
    assert result["title"] == "legacy GT"
    assert result["object_id"] == "567"


def test_get_file_falls_back_to_s3(mocked_aws):
    """DynamoDB miss for File-prefixed type → returns S3 data."""
    from data import dynamo as dynamo_mod

    body = {
        "clazz_name": "RuptureSet",
        "file_name": "legacy_ruptset.zip",
        "file_size": 1024,
        "created": "2021-05-02T00:00:00Z",
    }
    _put_s3_object(mocked_aws["s3"], "FileData/890/object.json", body)

    result = dynamo_mod.get_file(mocked_aws["dynamodb"], "890")
    assert result is not None
    assert result["clazz_name"] == "RuptureSet"
    assert result["file_name"] == "legacy_ruptset.zip"
    assert result["object_id"] == "890"


def test_get_table_falls_back_to_s3(mocked_aws):
    """get_table previously had no S3 fallback — now matches get_thing/get_file."""
    from data import dynamo as dynamo_mod

    body = {
        "clazz_name": "Table",
        "name": "Legacy MFD",
        "column_headers": ["mag", "rate"],
        "rows": [["6.0", "0.01"]],
    }
    _put_s3_object(mocked_aws["s3"], "TableData/4321/object.json", body)

    result = dynamo_mod.get_table(mocked_aws["dynamodb"], "4321")
    assert result is not None
    assert result["clazz_name"] == "Table"
    assert result["name"] == "Legacy MFD"
    assert result["object_id"] == "4321"


def test_get_thing_returns_none_when_neither_store_has_it(mocked_aws):
    from data import dynamo as dynamo_mod

    assert dynamo_mod.get_thing(mocked_aws["dynamodb"], "no-such-id") is None


# ── FIRST_DYNAMO_ID watermark helper ──────────────────────────────────────────


def test_is_pre_dynamo_file_id_classifies_old_ids_as_legacy():
    """Numeric IDs below 100000 (zero-padded) are pre-watermark."""
    from data.s3 import _is_pre_dynamo_file_id

    assert _is_pre_dynamo_file_id("123")
    assert _is_pre_dynamo_file_id("99999")


def test_is_pre_dynamo_file_id_classifies_post_watermark_ids_as_not_legacy():
    """Numeric IDs at or above 100000 are post-watermark (already in DynamoDB)."""
    from data.s3 import _is_pre_dynamo_file_id

    assert not _is_pre_dynamo_file_id("100000")
    assert not _is_pre_dynamo_file_id("100001")


def test_is_pre_dynamo_file_id_strips_dot_suffix():
    """Legacy IDs sometimes had a '.suffix' for revisions — only the numeric prefix is compared."""
    from data.s3 import _is_pre_dynamo_file_id

    assert _is_pre_dynamo_file_id("99999.1")
    assert not _is_pre_dynamo_file_id("100000.0")


# ── scan_s3_paginated ─────────────────────────────────────────────────────────


def test_scan_returns_empty_when_bucket_unset(monkeypatch):
    """scan_s3_paginated short-circuits when no bucket is configured."""
    from data import s3 as s3_mod

    monkeypatch.setattr(s3_mod, "S3_BUCKET_NAME", "")
    items, has_more, last = s3_mod.scan_s3_paginated("Thing", limit=5)
    assert items == []
    assert has_more is False
    assert last is None


def test_scan_returns_concrete_clazz_name_not_store_type(mocked_aws):
    """object_type must be the actual clazz_name so the relay GlobalID is dispatchable."""
    from data import s3 as s3_mod

    _put_s3_object(
        mocked_aws["s3"],
        "ThingData/100/object.json",
        {"clazz_name": "RuptureGenerationTask", "state": "done"},
    )
    _put_s3_object(
        mocked_aws["s3"],
        "ThingData/200/object.json",
        {"clazz_name": "GeneralTask", "title": "old GT"},
    )

    items, _has_more, _last = s3_mod.scan_s3_paginated("Thing", limit=10)
    type_map = {it["object_id"]: it["object_type"] for it in items}
    assert type_map == {"100": "RuptureGenerationTask", "200": "GeneralTask"}


def test_scan_skips_entries_without_clazz_name(mocked_aws):
    """Malformed object.json (no clazz_name) is skipped, not surfaced as a broken identity."""
    from data import s3 as s3_mod

    _put_s3_object(mocked_aws["s3"], "ThingData/300/object.json", {"state": "done"})
    _put_s3_object(
        mocked_aws["s3"], "ThingData/400/object.json", {"clazz_name": "AutomationTask"}
    )

    items, _, _ = s3_mod.scan_s3_paginated("Thing", limit=10)
    object_ids = {it["object_id"] for it in items}
    assert object_ids == {"400"}


def test_scan_file_data_applies_first_dynamo_id_watermark(mocked_aws):
    """File-prefixed IDs >= FIRST_DYNAMO_ID are filtered out (avoid double-yield vs DDB scan)."""
    from data import s3 as s3_mod

    _put_s3_object(
        mocked_aws["s3"], "FileData/99/object.json", {"clazz_name": "RuptureSet", "file_name": "old.zip"}
    )
    _put_s3_object(
        mocked_aws["s3"],
        "FileData/100001/object.json",
        {"clazz_name": "RuptureSet", "file_name": "new.zip"},
    )

    items, _, _ = s3_mod.scan_s3_paginated("File", limit=10)
    object_ids = {it["object_id"] for it in items}
    assert object_ids == {"99"}, "post-watermark file IDs must be filtered out"


def test_scan_thing_data_does_not_apply_watermark(mocked_aws):
    """The watermark filter is FileData-specific (matches legacy base_data.py:178)."""
    from data import s3 as s3_mod

    _put_s3_object(
        mocked_aws["s3"], "ThingData/100001/object.json", {"clazz_name": "GeneralTask", "title": "x"}
    )
    items, _, _ = s3_mod.scan_s3_paginated("Thing", limit=10)
    assert len(items) == 1
    assert items[0]["object_id"] == "100001"


def test_scan_pagination_cursor(mocked_aws):
    """StartAfter cursor advances through pages."""
    from data import s3 as s3_mod

    for i in range(1, 6):
        _put_s3_object(
            mocked_aws["s3"],
            f"ThingData/{i:05d}/object.json",
            {"clazz_name": "GeneralTask", "id": i},
        )

    page1, has_more, last = s3_mod.scan_s3_paginated("Thing", limit=2)
    assert len(page1) == 2
    assert has_more is True
    assert last == page1[-1]["object_id"]

    page2, _has_more2, _last2 = s3_mod.scan_s3_paginated("Thing", limit=2, after_id=last)
    page1_ids = {it["object_id"] for it in page1}
    page2_ids = {it["object_id"] for it in page2}
    assert page1_ids.isdisjoint(page2_ids), "cursor must advance — no overlap"
