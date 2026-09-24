"""
Thin Elasticsearch wrapper — index and search only.

Uses plain HTTP (requests) rather than the elasticsearch client library, matching
the spirit of the original search_manager.py which also falls back to raw requests
for the search call. Requests to an AWS domain (*.es.amazonaws.com) are SigV4
signed with the Lambda role's credentials; local docker ES is left unsigned.

Index name and endpoint are read from env vars at call time, but can be
overridden per-call for testing.
"""

import functools
import json
import logging
import os
import time
from dataclasses import dataclass, field
from urllib.parse import quote, urlparse

import boto3
import requests
from requests_aws4auth import AWS4Auth

log = logging.getLogger(__name__)

_TIMEOUT = 5  # seconds

# Logged on every failed index write. The CloudWatch metric filter behind the
# indexing alarm in serverless.yml matches on this exact string — change both
# together.
INDEX_FAILURE_MARKER = "ES_INDEX_FAILURE"

# Classes deliberately kept out of the search index (#378).
#
# OpenquakeHazardConfig: 2.19M objects, 1 of them in the index — they dropped
# out when the index was rebuilt in May 2024 and nobody missed them. The
# workflow that made them has since changed and no longer creates any, so this
# mainly keeps the backfill from adding 2.19M documents nobody searches for.
# create_openquake_hazard_config still exists in the schema, so it also covers
# a straggler written by an old client.
NOT_INDEXED: frozenset[str] = frozenset({"OpenquakeHazardConfig"})


def is_indexable(document: dict) -> bool:
    return document.get("clazz_name") not in NOT_INDEXED


# Read at call time (not import time) so testcontainers can set the env var
# after startup and have it picked up by all subsequent calls.
# Unset means indexing is off: the `if not endpoint` guards below skip cleanly.
# Do not default this to localhost — that turned a missing deploy config into
# three months of writes to nowhere (#378). Local dev sets ES_ENDPOINT explicitly.
def es_endpoint() -> str:
    return os.environ.get("ES_ENDPOINT", "")


def es_index() -> str:
    return os.environ.get("ES_INDEX", "toshi-index-mapped")


@functools.cache
def _aws_auth() -> AWS4Auth:
    # RefreshableCredentials, so a long-lived Lambda container keeps signing
    # after its first set of STS credentials expires.
    region = os.environ.get("ES_REGION") or os.environ.get("AWS_REGION", "ap-southeast-2")
    return AWS4Auth(refreshable_credentials=boto3.Session().get_credentials(), region=region, service="es")


def _auth_for(endpoint: str) -> AWS4Auth | None:
    host = urlparse(endpoint).hostname or ""
    return _aws_auth() if host.endswith(".es.amazonaws.com") else None


# Fields the index maps as objects, and the key a bare id takes in the modern
# shape. Objects from 2021-22 store these as plain id strings — e.g.
# "parents": ["9674zU9VY"] rather than [{"parent_id": "9674zU9VY"}] — which ES
# rejects with "tried to parse field [null] as object, but found a concrete
# value". That is why the legacy objects in #230 never made it into the index.
_ID_KEY_FOR_LIST = {
    "parents": "parent_id",
    "children": "child_id",
    "files": "file_id",
    "relations": "id",
    "predecessors": "id",
}


def _coerce_legacy_id_lists(doc: dict) -> None:
    """Rewrite bare id strings in object-mapped lists into the modern shape."""
    for name, id_key in _ID_KEY_FOR_LIST.items():
        value = doc.get(name)
        if isinstance(value, list) and any(not isinstance(item, dict) for item in value):
            doc[name] = [item if isinstance(item, dict) else {id_key: str(item)} for item in value]


def prepare_document(key: str, document: dict) -> tuple[str, dict]:
    """Return the (ES _id, body) that index_document and bulk_index write."""
    doc = dict(document)

    # relations_compressed hack — ES cannot handle fields that switch between
    # list and string across documents. Matches original search_manager.py:48-57.
    if doc.get("clazz_name") == "File" and isinstance(doc.get("relations"), str):
        doc["relations_compressed"] = doc.pop("relations")

    _coerce_legacy_id_lists(doc)

    # weka builds result links from _source.id, falling back to the ES _id
    # ("ThingData_...") when it is absent (#388). Graphene wrote `id` into every
    # body; the Strawberry path only sets object_id.
    if "id" not in doc and doc.get("object_id"):
        doc["id"] = doc["object_id"]

    return key.replace("/", "_"), doc


def index_document(
    key: str,
    document: dict,
    endpoint: str | None = None,
    index: str | None = None,
) -> None:
    """
    Index a document in Elasticsearch. No-op if endpoint is empty.
    Mirrors search_manager.py index_document(), including the
    relations_compressed hack for File objects.

    Never raises — search is best-effort and must not break writes — but every
    failure is logged at ERROR with INDEX_FAILURE_MARKER so it can be alarmed on.
    """
    if endpoint is None:
        endpoint = es_endpoint()
    if index is None:
        index = es_index()
    if not endpoint or not is_indexable(document):
        return

    safe_key, doc = prepare_document(key, document)
    url = f"{endpoint}/{index}/_doc/{safe_key}"
    try:
        resp = requests.put(url, json=doc, auth=_auth_for(endpoint), timeout=_TIMEOUT)
    except Exception as e:
        log.error("%s key=%s index=%s error=%r", INDEX_FAILURE_MARKER, safe_key, index, e)
        return
    if not resp.ok:
        log.error(
            "%s key=%s index=%s status=%s body=%.500s",
            INDEX_FAILURE_MARKER,
            safe_key,
            index,
            resp.status_code,
            resp.text,
        )


def count_by_clazz(endpoint: str, index: str, timeout: float = 60) -> dict[str, int]:
    """
    Document count per clazz_name in the index, for comparing with the object
    stores before a backfill (#378). Read-only.
    """
    # track_total_hits: ES7 caps hits.total at 10,000 without it.
    query = {
        "size": 0,
        "track_total_hits": True,
        "aggs": {"clazz": {"terms": {"field": "clazz_name.keyword", "size": 200}}},
    }
    resp = requests.post(f"{endpoint}/{index}/_search", json=query, auth=_auth_for(endpoint), timeout=timeout)
    resp.raise_for_status()
    body = resp.json()
    counts = {b["key"]: b["doc_count"] for b in body["aggregations"]["clazz"]["buckets"]}
    counts["TOTAL (all documents)"] = (
        body["hits"]["total"]["value"] if isinstance(body["hits"]["total"], dict) else body["hits"]["total"]
    )
    return counts


@dataclass
class BulkResult:
    indexed: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)  # (_id, reason)


_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})


def bulk_index(
    documents: list[tuple[str, dict]],
    endpoint: str,
    index: str,
    max_attempts: int = 5,
    backoff_seconds: float = 2.0,
    timeout: float = 60,
) -> BulkResult:
    """
    Write (key, document) pairs in one _bulk request. For the backfill (#378),
    not the live write path.

    Unlike index_document this raises: a backfill that cannot reach the domain
    should stop, not skip. Retries throttling (429) and gateway errors, both for
    the whole request and for items the cluster rejected under load; other
    per-item errors (e.g. mapping conflicts) are returned in BulkResult.failed.
    """
    result = BulkResult()
    # Already-prepared pairs come back through the 413 split; prepare only raw input.
    pending = [prepare_document(key, doc) for key, doc in documents if is_indexable(doc)]
    if not pending:
        return result
    url = f"{endpoint}/_bulk"
    auth = _auth_for(endpoint)

    for attempt in range(1, max_attempts + 1):
        body = "".join(
            json.dumps({"index": {"_index": index, "_id": safe_key}}) + "\n" + json.dumps(doc) + "\n"
            for safe_key, doc in pending
        )
        resp = requests.post(
            url, data=body.encode(), headers={"Content-Type": "application/x-ndjson"}, auth=auth, timeout=timeout
        )
        if resp.status_code == 413:
            # Batch over the domain's max request size. Halve and retry; a single
            # document that still will not fit is recorded, not retried forever.
            if len(pending) == 1:
                result.failed.append((pending[0][0], "413 Request Entity Too Large (single document)"))
                return result
            half = len(pending) // 2
            for part in (pending[:half], pending[half:]):
                part_result = bulk_index(
                    part, endpoint, index, max_attempts=max_attempts, backoff_seconds=backoff_seconds, timeout=timeout
                )
                result.indexed += part_result.indexed
                result.failed.extend(part_result.failed)
            return result
        if resp.status_code in _RETRYABLE_STATUS and attempt < max_attempts:
            time.sleep(backoff_seconds * 2 ** (attempt - 1))
            continue
        resp.raise_for_status()

        retry = []
        # A cluster write block (e.g. the disk flood-stage watermark) fails every
        # item with the same error and will not clear by retrying. Without this
        # a long backfill runs to completion writing nothing.
        blocked = next(
            (
                i["index"]["error"]
                for i in resp.json()["items"]
                if (i["index"].get("error") or {}).get("type") == "cluster_block_exception"
            ),
            None,
        )
        if blocked is not None:
            raise RuntimeError(f"Elasticsearch is refusing writes, fix the cluster before retrying: {blocked}")

        for (safe_key, doc), item in zip(pending, resp.json()["items"], strict=True):
            outcome = item["index"]
            if outcome.get("status", 500) < 300:
                result.indexed += 1
            elif outcome.get("status") == 429 and attempt < max_attempts:
                retry.append((safe_key, doc))
            else:
                result.failed.append((safe_key, json.dumps(outcome.get("error"))[:500]))
        if not retry:
            return result
        pending = retry
        time.sleep(backoff_seconds * 2 ** (attempt - 1))

    raise RuntimeError(f"_bulk still failing after {max_attempts} attempts: HTTP {resp.status_code}")


def search(
    term: str,
    endpoint: str | None = None,
    index: str | None = None,
) -> list[dict]:
    """
    Lucene query-string search. Returns list of raw _source dicts, each
    augmented with the ES _id so callers can identify Thing vs File.

    Mirrors search_manager.py search(), minus AWS auth (local docker only).
    """
    if endpoint is None:
        endpoint = es_endpoint()
    if index is None:
        index = es_index()
    if not endpoint:
        return []

    url = f"{endpoint}/{index}/_search?q={quote(term, safe='')}"
    try:
        resp = requests.get(url, auth=_auth_for(endpoint), timeout=_TIMEOUT).json()
        return [{"_id": hit["_id"], **hit["_source"]} for hit in resp.get("hits", {}).get("hits", [])]
    except Exception:
        return []
