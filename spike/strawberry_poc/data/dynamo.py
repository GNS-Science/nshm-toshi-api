"""
Thin boto3 wrapper for the three Toshi DynamoDB tables.

Replaces PynamoDB entirely. The DynamoDB table layout is unchanged:
  - object_id   (String, hash key)
  - object_type (String) — the Python class name, e.g. "GeneralTask"
  - object_content (String) — JSON-encoded payload dict

Reading existing data requires no migration — same tables, same JSON.
"""
import json
import os
from typing import Any

import boto3

from .ids import next_id

STAGE = os.environ.get("DEPLOYMENT_STAGE", "dev")
REGION = os.environ.get("REGION", "ap-southeast-2")


def _dynamodb(endpoint_url: str | None = None):
    kwargs: dict[str, Any] = {"region_name": REGION}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def _thing_table(dynamodb, stage: str = STAGE):
    return dynamodb.Table(f"ToshiThingObject-{stage}")


def _file_table(dynamodb, stage: str = STAGE):
    return dynamodb.Table(f"ToshiFileObject-{stage}")


# ── Type → table routing ─────────────────────────────────────────────────────
# Maps Strawberry type names to their DynamoDB table.
# ToshiFile is the Strawberry name; DynamoDB stores it as clazz_name="File".
THING_CLASSES: frozenset[str] = frozenset({
    "GeneralTask", "AutomationTask", "RuptureGenerationTask", "StrongMotionStation",
})
FILE_CLASSES: frozenset[str] = frozenset({
    "ToshiFile", "File", "SmsFile", "RuptureSet",
})


def get_object(dynamodb, type_name: str, object_id: str, stage: str = STAGE) -> dict | None:
    """Fetch a single object from the correct table by Strawberry type name."""
    if type_name in THING_CLASSES:
        return get_thing(dynamodb, object_id, stage)
    if type_name in FILE_CLASSES:
        return get_file(dynamodb, object_id, stage)
    return None


def es_key_for(type_name: str, object_id: str) -> str:
    """Return the Elasticsearch document key used during indexing."""
    prefix = "ThingData" if type_name in THING_CLASSES else "FileData"
    return f"{prefix}_{object_id}"


# ── Thing table (GeneralTask, AutomationTask, etc.) ──────────────────────────

def get_thing(dynamodb, object_id: str, stage: str = STAGE) -> dict | None:
    resp = _thing_table(dynamodb, stage).get_item(Key={"object_id": object_id})
    item = resp.get("Item")
    if not item:
        return None
    data = json.loads(item["object_content"])
    data["object_id"] = object_id
    return data


def create_thing(dynamodb, clazz_name: str, payload: dict, stage: str = STAGE) -> dict:
    from .search import index_document
    object_id = next_id(dynamodb, stage)
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    _thing_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": clazz_name,
        "object_content": json.dumps(payload),
    })
    payload["object_id"] = object_id
    index_document(f"ThingData_{object_id}", payload)
    return payload


def update_thing(dynamodb, object_id: str, payload: dict, stage: str = STAGE) -> dict | None:
    from .search import index_document
    existing = get_thing(dynamodb, object_id, stage)
    if existing is None:
        return None
    updated = {**existing, **{k: v for k, v in payload.items() if v is not None}}
    _thing_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": updated.get("clazz_name", ""),
        "object_content": json.dumps({k: v for k, v in updated.items() if k != "object_id"}),
    })
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
    if not item:
        return None
    data = json.loads(item["object_content"])
    data["object_id"] = object_id
    return data


def create_file(dynamodb, clazz_name: str, payload: dict, stage: str = STAGE) -> dict:
    from .search import index_document
    object_id = next_id(dynamodb, stage)
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    _file_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": clazz_name,
        "object_content": json.dumps(payload),
    })
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


# ── Relation helpers ──────────────────────────────────────────────────────────
# Relations are stored as embedded arrays within the parent objects, NOT as
# separate DynamoDB records. This mirrors the production pattern in
# file_relation_data.py and thing_relation_data.py.
#
# NOTE: Unlike production (which uses DynamoDB TransactWrite), these helpers
# use two separate puts. See README — "ID allocation transaction guard" — for
# the same caveat and the recommended boto3 fix for production use.

def _patch_thing(dynamodb, object_id: str, patch_fn, stage: str = STAGE) -> None:
    """Read a thing, apply patch_fn to its data dict, write it back."""
    table = _thing_table(dynamodb, stage)
    item = table.get_item(Key={"object_id": object_id}).get("Item")
    if not item:
        raise ValueError(f"Thing {object_id} not found")
    data = json.loads(item["object_content"])
    patch_fn(data)
    table.put_item(Item={
        "object_id": object_id,
        "object_type": item["object_type"],
        "object_content": json.dumps(data),
    })


def _patch_file(dynamodb, object_id: str, patch_fn, stage: str = STAGE) -> None:
    """Read a file, apply patch_fn to its data dict, write it back."""
    table = _file_table(dynamodb, stage)
    item = table.get_item(Key={"object_id": object_id}).get("Item")
    if not item:
        raise ValueError(f"File {object_id} not found")
    data = json.loads(item["object_content"])
    patch_fn(data)
    table.put_item(Item={
        "object_id": object_id,
        "object_type": item["object_type"],
        "object_content": json.dumps(data),
    })


def create_file_relation(
    dynamodb, thing_id: str, file_id: str, role: str, stage: str = STAGE
) -> None:
    """
    Append a file↔thing relation to both the Thing and File records.

    Thing.files  → [..., {"file_id": file_id, "file_role": role}]
    File.relations → [..., {"id": thing_id, "role": role}]
    """
    from .search import index_document
    _patch_thing(dynamodb, thing_id, lambda d: d.setdefault("files", []).append(
        {"file_id": file_id, "file_role": role}
    ), stage)
    _patch_file(dynamodb, file_id, lambda d: d.setdefault("relations", []).append(
        {"id": thing_id, "role": role}
    ), stage)
    # Re-index both sides so ES reflects the updated relation arrays
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
    """
    Append a parent↔child task relation to both Thing records.

    Parent.children → [..., {"child_id": child_id, "child_clazz": child_clazz}]
    Child.parents   → [..., {"parent_id": parent_id, "parent_clazz": parent_clazz}]
    """
    from .search import index_document
    _patch_thing(dynamodb, parent_id, lambda d: d.setdefault("children", []).append(
        {"child_id": child_id, "child_clazz": child_clazz}
    ), stage)
    _patch_thing(dynamodb, child_id, lambda d: d.setdefault("parents", []).append(
        {"parent_id": parent_id, "parent_clazz": parent_clazz}
    ), stage)
    # Re-index both sides so ES reflects the updated relation arrays
    parent_data = get_thing(dynamodb, parent_id, stage)
    if parent_data:
        index_document(f"ThingData_{parent_id}", parent_data)
    child_data = get_thing(dynamodb, child_id, stage)
    if child_data:
        index_document(f"ThingData_{child_id}", child_data)
