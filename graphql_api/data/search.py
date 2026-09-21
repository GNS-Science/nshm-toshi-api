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
import logging
import os
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
    if not endpoint:
        return

    doc = dict(document)

    # relations_compressed hack — ES cannot handle fields that switch between
    # list and string across documents. Matches original search_manager.py:48-57.
    if doc.get("clazz_name") == "File" and isinstance(doc.get("relations"), str):
        doc["relations_compressed"] = doc.pop("relations")

    safe_key = key.replace("/", "_")
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
