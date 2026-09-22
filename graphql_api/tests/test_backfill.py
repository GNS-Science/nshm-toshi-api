"""
Search index backfill (#378, #230).

- bulk_index: request shape, signing and retry behaviour, against requests_mock.
- run_backfill end to end: objects written to DynamoDB Local while indexing is
  off, then backfilled into the testcontainers ES, must come out identical to
  what the live write path would have indexed.
- iter_legacy_documents: the FIRST_DYNAMO_ID watermark, against moto S3.
"""

import json
import sys
import uuid
from pathlib import Path

import boto3
import pytest
import requests
from moto import mock_aws

from graphql_api.data import dynamo, search
from graphql_api.data.backfill import iter_dynamo_documents, iter_legacy_documents, run_backfill

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
import backfill_search_index  # noqa: E402

STAGE = "TEST"
LOCAL_EP = "http://localhost:9200"
AWS_EP = "https://search-nzshm22-toshi-api-es-prod-abc123.ap-southeast-2.es.amazonaws.com"


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(search.time, "sleep", lambda s: None)


def _bulk_response(*statuses, error=None):
    return {
        "errors": any(s >= 300 for s in statuses),
        "items": [{"index": {"status": s, **({"error": error} if s >= 300 else {})}} for s in statuses],
    }


# ── bulk_index ────────────────────────────────────────────────────────────────


def test_bulk_body_is_ndjson_with_prepared_documents(requests_mock):
    requests_mock.post(f"{LOCAL_EP}/_bulk", json=_bulk_response(200, 201))
    docs = [
        ("ThingData_1", {"clazz_name": "GeneralTask", "title": "a"}),
        ("FileData_2", {"clazz_name": "File", "relations": "compressed-blob"}),
    ]
    result = search.bulk_index(docs, endpoint=LOCAL_EP, index="idx")

    assert result.indexed == 2 and result.failed == []
    req = requests_mock.last_request
    assert req.headers["Content-Type"] == "application/x-ndjson"
    lines = [json.loads(line) for line in req.body.decode().splitlines()]
    assert lines[0] == {"index": {"_index": "idx", "_id": "ThingData_1"}}
    assert lines[1] == {"clazz_name": "GeneralTask", "title": "a"}
    # same relations_compressed hack as index_document
    assert lines[3] == {"clazz_name": "File", "relations_compressed": "compressed-blob"}
    assert "Authorization" not in req.headers


def test_bulk_to_aws_is_signed(requests_mock, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("ES_REGION", "ap-southeast-2")
    search._aws_auth.cache_clear()
    requests_mock.post(f"{AWS_EP}/_bulk", json=_bulk_response(200))
    try:
        search.bulk_index([("ThingData_1", {})], endpoint=AWS_EP, index="idx")
    finally:
        search._aws_auth.cache_clear()
    assert requests_mock.last_request.headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")


def test_bulk_retries_throttled_request(requests_mock, no_sleep):
    requests_mock.post(f"{LOCAL_EP}/_bulk", [{"status_code": 429}, {"json": _bulk_response(200)}])
    result = search.bulk_index([("ThingData_1", {})], endpoint=LOCAL_EP, index="idx")
    assert result.indexed == 1
    assert requests_mock.call_count == 2


def test_bulk_retries_only_rejected_items(requests_mock, no_sleep):
    requests_mock.post(
        f"{LOCAL_EP}/_bulk",
        [
            {"json": _bulk_response(201, 429, error={"type": "es_rejected_execution_exception"})},
            {"json": _bulk_response(201)},
        ],
    )
    result = search.bulk_index([("ThingData_1", {}), ("ThingData_2", {})], endpoint=LOCAL_EP, index="idx")
    assert result.indexed == 2
    retried = requests_mock.request_history[1].body.decode().splitlines()
    assert json.loads(retried[0])["index"]["_id"] == "ThingData_2"
    assert len(retried) == 2


def test_bulk_reports_item_errors_without_retrying(requests_mock, no_sleep):
    error = {"type": "mapper_parsing_exception", "reason": "failed to parse field [created]"}
    requests_mock.post(f"{LOCAL_EP}/_bulk", json=_bulk_response(201, 400, error=error))
    result = search.bulk_index([("ThingData_1", {}), ("ThingData_2", {})], endpoint=LOCAL_EP, index="idx")
    assert result.indexed == 1
    [(key, reason)] = result.failed
    assert key == "ThingData_2" and "mapper_parsing_exception" in reason
    assert requests_mock.call_count == 1


def test_bulk_raises_when_domain_keeps_failing(requests_mock, no_sleep):
    requests_mock.post(f"{LOCAL_EP}/_bulk", status_code=503)
    with pytest.raises(requests.HTTPError):
        search.bulk_index([("ThingData_1", {})], endpoint=LOCAL_EP, index="idx", max_attempts=3)
    assert requests_mock.call_count == 3


def test_bulk_raises_on_auth_failure(requests_mock):
    requests_mock.post(f"{LOCAL_EP}/_bulk", status_code=403)
    with pytest.raises(requests.HTTPError):
        search.bulk_index([("ThingData_1", {})], endpoint=LOCAL_EP, index="idx")
    assert requests_mock.call_count == 1


# ── run_backfill end to end (DynamoDB Local + ES containers) ──────────────────


@pytest.fixture
def fresh_index(es_endpoint):
    index = f"backfill-{uuid.uuid4().hex[:8]}"
    requests.put(f"{es_endpoint}/{index}", timeout=10).raise_for_status()
    yield index
    requests.delete(f"{es_endpoint}/{index}", timeout=10)


def _es_doc(endpoint, index, key):
    resp = requests.get(f"{endpoint}/{index}/_doc/{key}", timeout=10)
    return resp.json().get("_source") if resp.status_code == 200 else None


def test_backfill_indexes_unindexed_objects_as_live_path_would(dynamodb, es_endpoint, fresh_index, monkeypatch):
    monkeypatch.delenv("ES_ENDPOINT")  # indexing off, as in the outage
    thing = dynamo.create_thing(dynamodb, "GeneralTask", {"title": "missed", "created": "2026-07-01T00:00:00Z"})
    file = dynamo.create_file(dynamodb, "File", {"file_name": "f.zip", "created": "2026-07-02T00:00:00Z"})
    table = dynamo.create_table(dynamodb, "Table", {"name": "t", "created": "2026-07-03T00:00:00Z"})
    # push the file's relations past UNCOMPRESSED_LIMIT so they are stored compressed
    for i in range(dynamo.UNCOMPRESSED_LIMIT + 1):
        dynamo.create_file_relation(dynamodb, thing["object_id"], file["object_id"], f"role{i}")

    sources = [("dynamo", st, iter_dynamo_documents(dynamodb, st, STAGE)) for st in ("Thing", "File", "Table")]
    stats = run_backfill(sources, endpoint=es_endpoint, index=fresh_index, batch_size=2, execute=True)
    requests.post(f"{es_endpoint}/{fresh_index}/_refresh", timeout=10)

    assert stats.failed == []
    assert stats.indexed == 3
    # identical to what index_document gets on the live path: the get_* readers' output
    for key, expected in [
        (f"ThingData_{thing['object_id']}", dynamo.get_thing(dynamodb, thing["object_id"])),
        (f"FileData_{file['object_id']}", dynamo.get_file(dynamodb, file["object_id"])),
        (f"TableData_{table['object_id']}", dynamo.get_table(dynamodb, table["object_id"])),
    ]:
        assert _es_doc(es_endpoint, fresh_index, key) == search.prepare_document(key, expected)[1]
    assert len(_es_doc(es_endpoint, fresh_index, f"FileData_{file['object_id']}")["relations"]) == 101


def test_backfill_since_keeps_newer_and_undated(dynamodb, es_endpoint, fresh_index, monkeypatch):
    monkeypatch.delenv("ES_ENDPOINT")
    old = dynamo.create_thing(dynamodb, "GeneralTask", {"title": "old", "created": "2026-05-01T00:00:00Z"})
    new = dynamo.create_thing(dynamodb, "GeneralTask", {"title": "new", "created": "2026-06-12T09:00:00Z"})
    undated = dynamo.create_thing(dynamodb, "GeneralTask", {"title": "undated"})

    wanted = {old["object_id"], new["object_id"], undated["object_id"]}
    docs = (d for d in iter_dynamo_documents(dynamodb, "Thing", STAGE) if d[1]["object_id"] in wanted)
    stats = run_backfill(
        [("dynamo", "Thing", docs)], endpoint=es_endpoint, index=fresh_index, since="2026-06-12", execute=True
    )
    requests.post(f"{es_endpoint}/{fresh_index}/_refresh", timeout=10)

    assert stats.skipped_before_since == 1
    assert _es_doc(es_endpoint, fresh_index, f"ThingData_{old['object_id']}") is None
    assert _es_doc(es_endpoint, fresh_index, f"ThingData_{new['object_id']}") is not None
    assert _es_doc(es_endpoint, fresh_index, f"ThingData_{undated['object_id']}") is not None


def test_dry_run_writes_nothing(requests_mock):
    docs = iter([("ThingData_1", {"clazz_name": "GeneralTask"}), ("ThingData_2", {"clazz_name": "GeneralTask"})])
    stats = run_backfill([("dynamo", "Thing", docs)], endpoint=None, index="idx", execute=False)
    assert stats.seen[("dynamo", "Thing", "GeneralTask")] == 2
    assert stats.indexed == 0
    assert requests_mock.call_count == 0


# ── legacy S3 (moto) ──────────────────────────────────────────────────────────


def test_legacy_iterates_only_ids_below_watermark():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="legacy")
        s3.put_object(Bucket="legacy", Key="ThingData/1234/object.json", Body=json.dumps({"clazz_name": "GeneralTask"}))
        s3.put_object(Bucket="legacy", Key="ThingData/100001ABCDE/object.json", Body=json.dumps({"clazz_name": "X"}))
        s3.put_object(Bucket="legacy", Key="ThingData/5678/other.txt", Body=b"no object.json here")

        docs = list(iter_legacy_documents(s3, "legacy", "Thing"))

    assert docs == [("ThingData_1234", {"clazz_name": "GeneralTask", "object_id": "1234"})]


# ── CLI guard rails ───────────────────────────────────────────────────────────


def test_execute_requires_endpoint():
    with pytest.raises(SystemExit):
        backfill_search_index._parse_args(["--stage", "prod", "--execute"])


def test_refuses_to_write_to_missing_index(requests_mock):
    requests_mock.head(f"{LOCAL_EP}/toshi-index-mapped", status_code=404)
    with pytest.raises(SystemExit, match="refusing to create it"):
        backfill_search_index._check_index_exists(LOCAL_EP, "toshi-index-mapped")
