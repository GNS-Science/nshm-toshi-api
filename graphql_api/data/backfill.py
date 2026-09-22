"""
Rebuild the search index from the object stores (#378, #230).

The live write path indexes one object per mutation. Nothing re-indexes in
bulk, so objects written while indexing was broken (2026-06 onwards) and the
legacy S3-only objects that were never indexed (#230) are missing from weka
search. This module walks every object and writes it with the same key and
document shape the live path uses, so it is safe to re-run: each write
overwrites the document with the same _id.

Sources:
  - DynamoDB: every item in the Thing/File/Table tables for a stage.
  - Legacy S3: {store}Data/{id}/object.json. FileData/ also holds the uploaded
    content of every DynamoDB-era file (6.8M prefixes on prod), so File ids at
    or above FIRST_DYNAMO_ID are skipped by id, without fetching — the same
    rule as the legacy API. ThingData/ and TableData/ are small (~10k and ~8k
    prefixes on prod) and taken whole. Any id also in DynamoDB is written again
    from DynamoDB afterwards, so DynamoDB wins.

Driven by scripts/backfill_search_index.py.
"""

import json
import logging
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from .dynamo import _decompress_file_relations, _file_table, _table_table, _thing_table
from .s3 import _is_pre_dynamo_file_id
from .search import bulk_index

log = logging.getLogger(__name__)

STORES = ("Thing", "File", "Table")

_TABLE_FOR = {"Thing": _thing_table, "File": _file_table, "Table": _table_table}


def _normalise(store: str, object_id: str, data: dict) -> tuple[str, dict]:
    # Same shape get_thing / get_file / get_table return, which is what the
    # live write path indexes.
    data["object_id"] = object_id
    if store == "File":
        _decompress_file_relations(data)
    return f"{store}Data_{object_id}", data


def iter_dynamo_documents(dynamodb, store: str, stage: str) -> Iterator[tuple[str, dict]]:
    """Yield (es_key, document) for every item in one DynamoDB table."""
    table = _TABLE_FOR[store](dynamodb, stage)
    kwargs: dict[str, Any] = {}
    while True:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            yield _normalise(store, item["object_id"], json.loads(item["object_content"]))
        last = resp.get("LastEvaluatedKey")
        if not last:
            return
        kwargs["ExclusiveStartKey"] = last


def iter_legacy_documents(s3, bucket: str, store: str) -> Iterator[tuple[str, dict]]:
    """Yield (es_key, document) for every legacy S3 object in one store."""
    prefix = f"{store}Data/"
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            object_id = cp["Prefix"][len(prefix) :].rstrip("/")
            # Files only: the watermark is a string compare on the numeric
            # prefix, and would wrongly drop suffixed legacy Thing/Table ids.
            if store == "File" and not _is_pre_dynamo_file_id(object_id):
                continue
            try:
                body = s3.get_object(Bucket=bucket, Key=f"{prefix}{object_id}/object.json")["Body"].read()
            except s3.exceptions.NoSuchKey:
                log.warning("legacy %s/%s has no object.json; skipped", store, object_id)
                continue
            yield _normalise(store, object_id, json.loads(body))


@dataclass
class BackfillStats:
    seen: Counter = field(default_factory=Counter)  # (source, store, clazz_name) -> count
    skipped_before_since: int = 0
    skipped_filtered: int = 0
    indexed: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)


def numeric_id(object_id: str) -> int | None:
    """Leading integer of an object id ("123456ABCDE" -> 123456), or None.

    Ids come from one counter shared by all three tables (data/ids.py), so a
    larger id means created later, across stores. That is the only ordering
    File objects have — they carry no `created` field.
    """
    digits = ""
    for ch in object_id:
        if not ch.isdigit():
            break
        digits += ch
    return int(digits) if digits else None


def run_backfill(
    sources: list[tuple[str, str, Iterator[tuple[str, dict]]]],
    endpoint: str | None,
    index: str,
    since: str | None = None,
    clazz: set[str] | None = None,
    min_id: int | None = None,
    batch_size: int = 500,
    execute: bool = False,
    on_progress=None,
    progress_every: int = 10_000,
) -> BackfillStats:
    """
    Walk each (source, store, documents) and, if execute, bulk-write them.

    With execute=False nothing is written and endpoint is not contacted: the
    stats are a count of what would be indexed. since (ISO date) keeps only
    documents whose `created` is on or after it; documents without `created`
    are kept, since there is no way to tell they are not missing. clazz keeps
    only those clazz_names; min_id keeps only ids at or above that number
    (undated File objects are selected this way — see numeric_id).
    on_progress(stats, source, store) is called every progress_every documents read.
    """
    stats = BackfillStats()
    for source, store, documents in sources:
        batch: list[tuple[str, dict]] = []
        for n, (key, doc) in enumerate(documents):
            if on_progress and n and n % progress_every == 0:  # n documents read so far
                on_progress(stats, source, store)
            if clazz and doc.get("clazz_name") not in clazz:
                stats.skipped_filtered += 1
                continue
            if min_id is not None:
                this_id = numeric_id(doc.get("object_id", ""))
                if this_id is None or this_id < min_id:
                    stats.skipped_filtered += 1
                    continue
            created = doc.get("created")
            if since and isinstance(created, str) and created[: len(since)] < since:
                stats.skipped_before_since += 1
                continue
            stats.seen[(source, store, doc.get("clazz_name") or "?")] += 1
            if not execute:
                continue
            batch.append((key, doc))
            if len(batch) >= batch_size:
                _flush(batch, endpoint, index, stats)
                batch = []
        if execute and batch:
            _flush(batch, endpoint, index, stats)
    return stats


def _flush(batch, endpoint, index, stats: BackfillStats) -> None:
    result = bulk_index(batch, endpoint=endpoint, index=index)
    stats.indexed += result.indexed
    stats.failed.extend(result.failed)
