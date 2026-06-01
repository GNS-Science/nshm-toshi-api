"""
Thin Elasticsearch wrapper — index and search only.

Uses plain HTTP (requests) rather than the elasticsearch client library, matching
the spirit of the original search_manager.py which also falls back to raw requests
for the search call. No AWS auth needed for local docker ES.

Index name and endpoint are read from env vars at import time, but can be
overridden per-call for testing.
"""

import os

import requests

_TIMEOUT = 5  # seconds


# Read at call time (not import time) so testcontainers can set the env var
# after startup and have it picked up by all subsequent calls.
def es_endpoint() -> str:
    return os.environ.get("ES_ENDPOINT", "http://localhost:9200")


def es_index() -> str:
    return os.environ.get("ES_INDEX", "toshi-index-mapped")


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
        requests.put(url, json=doc, timeout=_TIMEOUT)
    except Exception:
        pass  # non-fatal — search is best-effort, never break writes


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

    url = f"{endpoint}/{index}/_search?q={term}"
    try:
        resp = requests.get(url, timeout=_TIMEOUT).json()
        return [{"_id": hit["_id"], **hit["_source"]} for hit in resp.get("hits", {}).get("hits", [])]
    except Exception:
        return []
