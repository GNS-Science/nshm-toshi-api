"""
Unit tests for graphql_api.data.search.index_document — the write path to
Elasticsearch (#378).

No live ES: requests are intercepted with requests_mock, so these run without
the testcontainers fixtures.
"""

import json
import logging

import pytest
import requests

from graphql_api.data import search

LOCAL_EP = "http://localhost:9200"
AWS_EP = "https://search-nzshm22-toshi-api-es-prod-abc123.ap-southeast-2.es.amazonaws.com"
INDEX = "toshi_index_mapped"


@pytest.fixture(autouse=True)
def fake_aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "token")
    monkeypatch.delenv("AWS_SECURITY_TOKEN", raising=False)  # conftest sets it; botocore prefers it
    monkeypatch.setenv("ES_REGION", "ap-southeast-2")
    search._aws_auth.cache_clear()
    yield
    search._aws_auth.cache_clear()


def test_endpoint_defaults_to_empty_when_unset(monkeypatch):
    """Unconfigured means off — not localhost (the #378 outage was writes to localhost:9200)."""
    monkeypatch.delenv("ES_ENDPOINT", raising=False)
    assert search.es_endpoint() == ""


def test_empty_endpoint_skips_indexing(requests_mock, caplog):
    search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint="", index=INDEX)
    assert requests_mock.call_count == 0
    assert search.INDEX_FAILURE_MARKER not in caplog.text


def test_local_endpoint_is_not_signed(requests_mock):
    requests_mock.put(f"{LOCAL_EP}/{INDEX}/_doc/ThingData_1", status_code=201)
    search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint=LOCAL_EP, index=INDEX)
    assert requests_mock.call_count == 1
    assert "Authorization" not in requests_mock.last_request.headers


def test_aws_endpoint_is_sigv4_signed(requests_mock):
    requests_mock.put(f"{AWS_EP}/{INDEX}/_doc/ThingData_1", status_code=201)
    search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint=AWS_EP, index=INDEX)
    assert requests_mock.call_count == 1
    auth = requests_mock.last_request.headers["Authorization"]
    assert auth.startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")
    assert "/ap-southeast-2/es/aws4_request" in auth
    assert requests_mock.last_request.headers["X-Amz-Security-Token"] == "token"


def test_success_logs_nothing(requests_mock, caplog):
    requests_mock.put(f"{LOCAL_EP}/{INDEX}/_doc/ThingData_1", status_code=200)
    with caplog.at_level(logging.WARNING, logger=search.__name__):
        search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint=LOCAL_EP, index=INDEX)
    assert caplog.records == []


def test_http_error_status_is_logged_not_raised(requests_mock, caplog):
    """A 403 from the domain access policy is a failure, not a success."""
    requests_mock.put(f"{AWS_EP}/{INDEX}/_doc/ThingData_1", status_code=403, text='{"message":"denied"}')
    with caplog.at_level(logging.ERROR, logger=search.__name__):
        search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint=AWS_EP, index=INDEX)
    [record] = caplog.records
    assert record.levelno == logging.ERROR
    assert search.INDEX_FAILURE_MARKER in record.getMessage()
    assert "ThingData_1" in record.getMessage()
    assert "403" in record.getMessage()


def test_connection_error_is_logged_not_raised(requests_mock, caplog):
    requests_mock.put(f"{LOCAL_EP}/{INDEX}/_doc/ThingData_1", exc=requests.exceptions.ConnectionError)
    with caplog.at_level(logging.ERROR, logger=search.__name__):
        search.index_document("ThingData_1", {"clazz_name": "GeneralTask"}, endpoint=LOCAL_EP, index=INDEX)
    [record] = caplog.records
    assert search.INDEX_FAILURE_MARKER in record.getMessage()
    assert "ThingData_1" in record.getMessage()


def test_excluded_class_is_not_indexed(requests_mock):
    """OpenquakeHazardConfig stays out of the index by choice (#378)."""
    search.index_document("ThingData_1", {"clazz_name": "OpenquakeHazardConfig"}, endpoint=LOCAL_EP, index=INDEX)
    assert requests_mock.call_count == 0


def test_excluded_class_is_dropped_from_bulk(requests_mock):
    requests_mock.post(f"{LOCAL_EP}/_bulk", json={"errors": False, "items": [{"index": {"status": 201}}]})
    result = search.bulk_index(
        [
            ("ThingData_1", {"clazz_name": "OpenquakeHazardConfig"}),
            ("ThingData_2", {"clazz_name": "OpenquakeHazardTask"}),
        ],
        endpoint=LOCAL_EP,
        index=INDEX,
    )
    assert result.indexed == 1
    ids = [json.loads(line)["index"]["_id"] for line in requests_mock.last_request.body.decode().splitlines()[::2]]
    assert ids == ["ThingData_2"]


def test_bulk_of_only_excluded_classes_makes_no_request(requests_mock):
    result = search.bulk_index(
        [("ThingData_1", {"clazz_name": "OpenquakeHazardConfig"})], endpoint=LOCAL_EP, index=INDEX
    )
    assert result.indexed == 0 and requests_mock.call_count == 0


# ── legacy shapes (#230) ──────────────────────────────────────────────────────
# Objects from 2021-22 store parents/children/files as bare id strings. ES maps
# those fields as objects and rejects the document, which is why they are absent
# from the index. Fixtures are real prod records (ThingData/10005y9Zn, 10001HzGWM).


def test_bare_id_lists_become_objects():
    _, doc = search.prepare_document(
        "ThingData_10005y9Zn",
        {
            "clazz_name": "RuptureGenerationTask",
            "parents": ["947PkKMv"],
            "files": ["3152svdMW", "3198EQUfp"],
        },
    )
    assert doc["parents"] == [{"parent_id": "947PkKMv"}]
    assert doc["files"] == [{"file_id": "3152svdMW"}, {"file_id": "3198EQUfp"}]


def test_modern_shape_is_untouched():
    files = [{"file_id": "24889.0SN88A", "file_role": "read"}]
    parents = [{"parent_id": "9674zU9VY", "parent_clazz": "GeneralTask"}]
    _, doc = search.prepare_document(
        "ThingData_10001HzGWM", {"clazz_name": "AutomationTask", "files": files, "parents": parents}
    )
    assert doc["files"] == files
    assert doc["parents"] == parents


def test_mixed_list_coerces_only_the_bare_entries():
    _, doc = search.prepare_document(
        "ThingData_1", {"clazz_name": "AutomationTask", "files": ["3152svdMW", {"file_id": "x", "file_role": "write"}]}
    )
    assert doc["files"] == [{"file_id": "3152svdMW"}, {"file_id": "x", "file_role": "write"}]


def test_file_relations_coerced_after_decompression_hack():
    _, doc = search.prepare_document("FileData_1", {"clazz_name": "File", "relations": ["9674zU9VY"]})
    assert doc["relations"] == [{"id": "9674zU9VY"}]
    _, compressed = search.prepare_document("FileData_2", {"clazz_name": "File", "relations": "compressed-blob"})
    assert compressed["relations_compressed"] == "compressed-blob"
    assert "relations" not in compressed
