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
    object_id = next_id(dynamodb, stage)
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    _thing_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": clazz_name,
        "object_content": json.dumps(payload),
    })
    payload["object_id"] = object_id
    return payload


def update_thing(dynamodb, object_id: str, payload: dict, stage: str = STAGE) -> dict | None:
    existing = get_thing(dynamodb, object_id, stage)
    if existing is None:
        return None
    updated = {**existing, **{k: v for k, v in payload.items() if v is not None}}
    _thing_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": updated.get("clazz_name", ""),
        "object_content": json.dumps({k: v for k, v in updated.items() if k != "object_id"}),
    })
    return updated


def list_things(dynamodb, clazz_name: str, stage: str = STAGE, limit: int = 100) -> list[dict]:
    resp = _thing_table(dynamodb, stage).scan(
        FilterExpression="object_type = :t",
        ExpressionAttributeValues={":t": clazz_name},
        Limit=limit,
    )
    results = []
    for item in resp.get("Items", []):
        data = json.loads(item["object_content"])
        data["object_id"] = item["object_id"]
        results.append(data)
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
    object_id = next_id(dynamodb, stage)
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["clazz_name"] = clazz_name
    _file_table(dynamodb, stage).put_item(Item={
        "object_id": object_id,
        "object_type": clazz_name,
        "object_content": json.dumps(payload),
    })
    payload["object_id"] = object_id
    return payload


def list_files(dynamodb, clazz_name: str, stage: str = STAGE, limit: int = 100) -> list[dict]:
    resp = _file_table(dynamodb, stage).scan(
        FilterExpression="object_type = :t",
        ExpressionAttributeValues={":t": clazz_name},
        Limit=limit,
    )
    results = []
    for item in resp.get("Items", []):
        data = json.loads(item["object_content"])
        data["object_id"] = item["object_id"]
        results.append(data)
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
    _patch_thing(dynamodb, thing_id, lambda d: d.setdefault("files", []).append(
        {"file_id": file_id, "file_role": role}
    ), stage)
    _patch_file(dynamodb, file_id, lambda d: d.setdefault("relations", []).append(
        {"id": thing_id, "role": role}
    ), stage)


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
    _patch_thing(dynamodb, parent_id, lambda d: d.setdefault("children", []).append(
        {"child_id": child_id, "child_clazz": child_clazz}
    ), stage)
    _patch_thing(dynamodb, child_id, lambda d: d.setdefault("parents", []).append(
        {"parent_id": parent_id, "parent_clazz": parent_clazz}
    ), stage)
