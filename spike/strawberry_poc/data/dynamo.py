"""
Thin boto3 wrapper for the three Toshi DynamoDB tables.

Replaces PynamoDB entirely. The DynamoDB table layout is unchanged:
  - object_id   (String, hash key)
  - object_type (String) — the Python class name, e.g. "GeneralTask"
  - object_content (String) — JSON-encoded payload dict

Reading existing data requires no migration — same tables, same JSON.
"""

import json
import logging
import os
import random
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .ids import append_uniq, read_current_id
from .search import index_document

logger = logging.getLogger(__name__)

STAGE = os.environ.get("DEPLOYMENT_STAGE", "dev").upper()
REGION = os.environ.get("REGION", "ap-southeast-2")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
DB_READ_ONLY = os.environ.get("DB_READ_ONLY", "") not in ("", "0")


def _assert_writable() -> None:
    if DB_READ_ONLY:
        raise RuntimeError("Aborting write: DB_READ_ONLY is set")


def _dynamodb(endpoint_url: str | None = None):
    kwargs: dict[str, Any] = {"region_name": REGION}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def _thing_table(dynamodb, stage: str = STAGE):
    return dynamodb.Table(f"ToshiThingObject-{stage}")


def _file_table(dynamodb, stage: str = STAGE):
    return dynamodb.Table(f"ToshiFileObject-{stage}")


def _table_table(dynamodb, stage: str = STAGE):
    return dynamodb.Table(f"ToshiTableObject-{stage}")


# ── Type → table routing ─────────────────────────────────────────────────────
THING_CLASSES: frozenset[str] = frozenset(
    {
        "GeneralTask",
        "AutomationTask",
        "RuptureGenerationTask",
        "StrongMotionStation",
        "OpenquakeHazardTask",
        "OpenquakeHazardSolution",
        "OpenquakeHazardConfig",
    }
)
FILE_CLASSES: frozenset[str] = frozenset(
    {
        "ToshiFile",
        "File",
        "SmsFile",
        "RuptureSet",
        "InversionSolution",
        "ScaledInversionSolution",
        "AggregateInversionSolution",
        "TimeDependentInversionSolution",
        "InversionSolutionNrml",
    }
)
# Extend as table-backed models are added to the schema.
TABLE_CLASSES: frozenset[str] = frozenset(
    {
        "Table",
        "GroundMotionTable",
        "GriddedHazard",
    }
)


def get_object(dynamodb, type_name: str, object_id: str, stage: str = STAGE) -> dict | None:
    """Fetch a single object from the correct table by Strawberry type name."""
    if type_name in THING_CLASSES:
        return get_thing(dynamodb, object_id, stage)
    if type_name in FILE_CLASSES:
        return get_file(dynamodb, object_id, stage)
    if type_name in TABLE_CLASSES:
        return get_table(dynamodb, object_id, stage)
    return None


def es_key_for(type_name: str, object_id: str) -> str:
    """Return the Elasticsearch document key used during indexing."""
    if type_name in THING_CLASSES:
        return f"ThingData_{object_id}"
    if type_name in TABLE_CLASSES:
        return f"TableData_{object_id}"
    return f"FileData_{object_id}"


# ── S3 fallback (legacy objects not yet migrated to DynamoDB) ─────────────────


def _from_s3(object_id: str, prefix: str) -> dict | None:
    """
    Read object.json from S3 for legacy objects not in DynamoDB.
    Key format: {prefix}/{object_id}/object.json  (matches base_data._from_s3).
    Returns None if S3_BUCKET_NAME is unset or the object doesn't exist.
    """
    if not S3_BUCKET_NAME:
        return None
    key = f"{prefix}/{object_id}/object.json"
    try:
        s3 = boto3.client("s3", region_name=REGION)
        obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        return json.loads(obj["Body"].read())
    except Exception as exc:
        logger.debug("S3 fallback miss for %s/%s: %s", prefix, object_id, exc)
        return None


# ── Atomic ID allocation ──────────────────────────────────────────────────────


def _atomic_put(dynamodb, dest_table_name: str, clazz_name: str, payload: dict, stage: str) -> str:
    """
    Atomically increment ToshiIdentity and write the object in a single
    transact_write_items call. A conditional check on the counter value
    ensures no two concurrent writers get the same ID; TransactionCanceledException
    triggers an exponential-backoff retry with a fresh counter read.

    Mirrors base_data._write_object / PynamoDB TransactWrite pattern.
    Requires real DynamoDB (Local or AWS) — moto 5.x does not support
    transact_write_items across two tables.
    """
    # boto3 resource.meta.client has a serialization issue when used for raw
    # low-level calls — create a fresh client from the same endpoint instead.
    endpoint_url = str(dynamodb.meta.client.meta.endpoint_url)
    client = boto3.client("dynamodb", endpoint_url=endpoint_url, region_name=REGION)

    for attempt in range(10):
        current_id = read_current_id(dynamodb, stage)
        object_id = append_uniq(current_id)
        try:
            client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": f"ToshiIdentity-{stage}",
                            "Key": {"table_name": {"S": stage}},
                            "UpdateExpression": "SET object_id = object_id + :inc",
                            "ConditionExpression": "object_id = :cur",
                            "ExpressionAttributeValues": {
                                ":inc": {"N": "1"},
                                ":cur": {"N": str(current_id)},
                            },
                        }
                    },
                    {
                        "Put": {
                            "TableName": dest_table_name,
                            "Item": {
                                "object_id": {"S": object_id},
                                "object_type": {"S": clazz_name},
                                "object_content": {"S": json.dumps(payload)},
                            },
                        }
                    },
                ]
            )
            return object_id
        except ClientError as exc:
            if exc.response["Error"]["Code"] not in ("TransactionCanceledException", "TransactionConflictException"):
                raise
            wait = (2**attempt) * 0.05 + random.uniform(0, 0.05)
            logger.debug("TransactionCanceledException attempt %d; retrying in %.2fs", attempt, wait)
            time.sleep(wait)

    raise RuntimeError("Failed to write object after 10 attempts (persistent TransactionCanceledException)")


# ── Thing table (GeneralTask, AutomationTask, etc.) ──────────────────────────


def get_thing(dynamodb, object_id: str, stage: str = STAGE) -> dict | None:
    resp = _thing_table(dynamodb, stage).get_item(Key={"object_id": object_id})
    item = resp.get("Item")
    if item:
        data = json.loads(item["object_content"])
        data["object_id"] = object_id
        return data
    data = _from_s3(object_id, "ThingData")
    if data is not None:
        data["object_id"] = object_id
    return data


def create_thing(dynamodb, clazz_name: str, payload: dict, stage: str = STAGE) -> dict:
    _assert_writable()
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    object_id = _atomic_put(dynamodb, f"ToshiThingObject-{stage}", clazz_name, payload, stage)
    payload["object_id"] = object_id
    index_document(f"ThingData_{object_id}", payload)
    return payload


def update_thing(dynamodb, object_id: str, payload: dict, stage: str = STAGE) -> dict | None:
    _assert_writable()
    existing = get_thing(dynamodb, object_id, stage)
    if existing is None:
        return None
    updated = {**existing, **{k: v for k, v in payload.items() if v is not None}}
    _thing_table(dynamodb, stage).put_item(
        Item={
            "object_id": object_id,
            "object_type": updated.get("clazz_name", ""),
            "object_content": json.dumps({k: v for k, v in updated.items() if k != "object_id"}),
        }
    )
    index_document(f"ThingData_{object_id}", updated)
    return updated


def list_things(dynamodb, clazz_name: str, stage: str = STAGE) -> list[dict]:
    """Return all items of clazz_name, exhausting DynamoDB pages."""
    table = _thing_table(dynamodb, stage)
    kwargs: dict[str, Any] = {
        "FilterExpression": "object_type = :t",
        "ExpressionAttributeValues": {":t": clazz_name},
    }
    results = []
    while True:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            data = json.loads(item["object_content"])
            data["object_id"] = item["object_id"]
            results.append(data)
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last
    return results


# ── File table (RuptureSet, InversionSolution, File, etc.) ───────────────────


def get_file(dynamodb, object_id: str, stage: str = STAGE) -> dict | None:
    resp = _file_table(dynamodb, stage).get_item(Key={"object_id": object_id})
    item = resp.get("Item")
    if item:
        data = json.loads(item["object_content"])
        data["object_id"] = object_id
        return data
    data = _from_s3(object_id, "FileData")
    if data is not None:
        data["object_id"] = object_id
    return data


def create_file(dynamodb, clazz_name: str, payload: dict, stage: str = STAGE) -> dict:
    _assert_writable()
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    object_id = _atomic_put(dynamodb, f"ToshiFileObject-{stage}", clazz_name, payload, stage)
    payload["object_id"] = object_id
    index_document(f"FileData_{object_id}", payload)
    return payload


def list_files(dynamodb, clazz_name: str, stage: str = STAGE) -> list[dict]:
    """Return all items of clazz_name, exhausting DynamoDB pages."""
    table = _file_table(dynamodb, stage)
    kwargs: dict[str, Any] = {
        "FilterExpression": "object_type = :t",
        "ExpressionAttributeValues": {":t": clazz_name},
    }
    results = []
    while True:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            data = json.loads(item["object_content"])
            data["object_id"] = item["object_id"]
            results.append(data)
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last
    return results


# ── Table table (GroundMotionTable, GriddedHazard, etc.) ─────────────────────


def get_table(dynamodb, object_id: str, stage: str = STAGE) -> dict | None:
    resp = _table_table(dynamodb, stage).get_item(Key={"object_id": object_id})
    item = resp.get("Item")
    if not item:
        return None
    data = json.loads(item["object_content"])
    data["object_id"] = object_id
    return data


def create_table(dynamodb, clazz_name: str, payload: dict, stage: str = STAGE) -> dict:
    _assert_writable()
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    object_id = _atomic_put(dynamodb, f"ToshiTableObject-{stage}", clazz_name, payload, stage)
    payload["object_id"] = object_id
    index_document(f"TableData_{object_id}", payload)
    return payload


def list_tables(dynamodb, clazz_name: str, stage: str = STAGE) -> list[dict]:
    """Return all items of clazz_name, exhausting DynamoDB pages."""
    table = _table_table(dynamodb, stage)
    kwargs: dict[str, Any] = {
        "FilterExpression": "object_type = :t",
        "ExpressionAttributeValues": {":t": clazz_name},
    }
    results = []
    while True:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            data = json.loads(item["object_content"])
            data["object_id"] = item["object_id"]
            results.append(data)
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last
    return results


# ── Paginated scan (for object_identities query) ──────────────────────────────


def scan_objects_paginated(
    dynamodb,
    object_type: str,
    limit: int = 5,
    after_id: str | None = None,
    stage: str = STAGE,
) -> tuple[list[dict], bool, str | None]:
    """Page through one DynamoDB table filtered to object_type.

    Returns (items, has_more, last_object_id).  Uses ExclusiveStartKey for
    efficient forward pagination — after_id is the object_id of the last item
    from the previous page (decoded from the cursor by the caller).
    """
    if object_type in THING_CLASSES:
        table = _thing_table(dynamodb, stage)
    elif object_type in FILE_CLASSES:
        table = _file_table(dynamodb, stage)
    elif object_type in TABLE_CLASSES:
        table = _table_table(dynamodb, stage)
    else:
        return [], False, None

    results: list[dict] = []
    last_id: str | None = None
    kwargs: dict[str, Any] = {
        "FilterExpression": "object_type = :t",
        "ExpressionAttributeValues": {":t": object_type},
    }
    if after_id:
        kwargs["ExclusiveStartKey"] = {"object_id": after_id}

    while len(results) < limit:
        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            data = json.loads(item["object_content"])
            data["object_id"] = item["object_id"]
            results.append(data)
            last_id = item["object_id"]
            if len(results) >= limit:
                break
        last_key = resp.get("LastEvaluatedKey")
        if not last_key or len(results) >= limit:
            break
        kwargs["ExclusiveStartKey"] = last_key

    has_more = len(results) >= limit
    return results[:limit], has_more, last_id


# ── Relation helpers ──────────────────────────────────────────────────────────
# Relations are stored as embedded arrays within the parent objects, NOT as
# separate DynamoDB records. This mirrors the production pattern in
# file_relation_data.py and thing_relation_data.py.


def _patch_thing(dynamodb, object_id: str, patch_fn, stage: str = STAGE) -> None:
    """Read a thing, apply patch_fn to its data dict, write it back."""
    table = _thing_table(dynamodb, stage)
    item = table.get_item(Key={"object_id": object_id}).get("Item")
    if not item:
        raise ValueError(f"Thing {object_id} not found")
    data = json.loads(item["object_content"])
    patch_fn(data)
    table.put_item(
        Item={
            "object_id": object_id,
            "object_type": item["object_type"],
            "object_content": json.dumps(data),
        }
    )


def _patch_file(dynamodb, object_id: str, patch_fn, stage: str = STAGE) -> None:
    """Read a file, apply patch_fn to its data dict, write it back."""
    table = _file_table(dynamodb, stage)
    item = table.get_item(Key={"object_id": object_id}).get("Item")
    if not item:
        raise ValueError(f"File {object_id} not found")
    data = json.loads(item["object_content"])
    patch_fn(data)
    table.put_item(
        Item={
            "object_id": object_id,
            "object_type": item["object_type"],
            "object_content": json.dumps(data),
        }
    )


def create_file_relation(dynamodb, thing_id: str, file_id: str, role: str, stage: str = STAGE) -> None:
    _assert_writable()
    """
    Append a file↔thing relation to both the Thing and File records.

    Thing.files  → [..., {"file_id": file_id, "file_role": role}]
    File.relations → [..., {"id": thing_id, "role": role}]
    """
    _patch_thing(
        dynamodb, thing_id, lambda d: d.setdefault("files", []).append({"file_id": file_id, "file_role": role}), stage
    )
    _patch_file(
        dynamodb, file_id, lambda d: d.setdefault("relations", []).append({"id": thing_id, "role": role}), stage
    )
    thing_data = get_thing(dynamodb, thing_id, stage)
    if thing_data:
        index_document(f"ThingData_{thing_id}", thing_data)
    file_data = get_file(dynamodb, file_id, stage)
    if file_data:
        index_document(f"FileData_{file_id}", file_data)


def create_task_relation(
    dynamodb,
    parent_id: str,
    parent_clazz: str,
    child_id: str,
    child_clazz: str,
    stage: str = STAGE,
) -> None:
    _assert_writable()
    """
    Append a parent↔child task relation to both Thing records.

    Parent.children → [..., {"child_id": child_id, "child_clazz": child_clazz}]
    Child.parents   → [..., {"parent_id": parent_id, "parent_clazz": parent_clazz}]
    """
    _patch_thing(
        dynamodb,
        parent_id,
        lambda d: d.setdefault("children", []).append({"child_id": child_id, "child_clazz": child_clazz}),
        stage,
    )
    _patch_thing(
        dynamodb,
        child_id,
        lambda d: d.setdefault("parents", []).append({"parent_id": parent_id, "parent_clazz": parent_clazz}),
        stage,
    )
    parent_data = get_thing(dynamodb, parent_id, stage)
    if parent_data:
        index_document(f"ThingData_{parent_id}", parent_data)
    child_data = get_thing(dynamodb, child_id, stage)
    if child_data:
        index_document(f"ThingData_{child_id}", child_data)
