"""S3 helpers — presigned download URLs and legacy object enumeration."""

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
REGION = os.environ.get("REGION", "ap-southeast-2")
_URL_TTL = int(os.environ.get("URL_DEFAULT_TTL", "3600"))

# IDs below this watermark are "pre-DynamoDB era" — they live only in S3.
# IDs >= this watermark might also exist in S3 as dual-writes from the
# migration period, so the legacy iterator skips them when enumerating
# FileData to avoid double-yielding. Matches graphql_api/config.py.
FIRST_DYNAMO_ID = int(os.environ.get("FIRST_DYNAMO_ID", "100000"))


def presigned_download_url(object_id: str, file_name: str | None) -> str | None:
    """Return a presigned S3 GET URL for FileData/{object_id}/{file_name}.

    Mirrors file_data.py:get_presigned_url. Returns None if S3 is not configured
    or file_name is unknown (object not yet uploaded).
    """
    if not S3_BUCKET_NAME or not file_name:
        return None
    key = f"FileData/{object_id}/{file_name}"
    s3 = boto3.client("s3", region_name=REGION)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=_URL_TTL,
    )


def presigned_post_for_file(object_id: str, file_name: str, md5_digest: str | None) -> dict | None:
    """Generate a presigned-POST payload for client-side upload to S3.

    Mirrors `graphql_api/data/file_data.py:57-70`. Returns the boto3
    `generate_presigned_post` dict `{"url": ..., "fields": {...}}` or
    None when S3 is not configured.

    Also writes a "placeholder_to_be_overwritten" object at the same key
    so the legacy "object exists" assumption holds before the client
    PUTs the real bytes (matches file_data.py:56).
    """
    if not S3_BUCKET_NAME or not file_name:
        return None
    key = f"FileData/{object_id}/{file_name}"
    s3 = boto3.client("s3", region_name=REGION)
    try:
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body="placeholder_to_be_overwritten")
    except Exception as exc:
        logger.debug("presigned_post_for_file: placeholder put failed for %s: %s", key, exc)
        return None
    return s3.generate_presigned_post(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Fields={
            "acl": "public-read",
            "Content-MD5": md5_digest or "",
            "Content-Type": "binary/octet-stream",
        },
        Conditions=[
            {"acl": "public-read"},
            ["starts-with", "$Content-Type", ""],
            ["starts-with", "$Content-MD5", ""],
        ],
    )


def _read_clazz_name(s3, bucket: str, key: str) -> str | None:
    """Fetch object.json and return its clazz_name field, or None on miss/error."""
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = json.loads(obj["Body"].read())
        return body.get("clazz_name")
    except Exception as exc:
        logger.debug("S3 clazz_name fetch failed for %s: %s", key, exc)
        return None


def _is_pre_dynamo_file_id(object_id: str) -> bool:
    """True if the object_id is a pre-DynamoDB-migration ID for FileData.

    Mirrors graphql_api/data/base_data.py:178-183 — pads the numeric
    leading segment to FIRST_DYNAMO_ID's width with leading spaces and
    string-compares. IDs sorting as ' 12345' < '100000' pass; '100001abc'
    and similar dual-writes are filtered out (already in DynamoDB).
    """
    numeric_part = object_id.split(".")[0]
    keylen = len(str(FIRST_DYNAMO_ID))
    padded = f"{numeric_part:>{keylen}}"
    return padded < str(FIRST_DYNAMO_ID)


def scan_s3_paginated(
    store_type: str,
    limit: int = 5,
    after_id: str | None = None,
) -> tuple[list[dict], bool, str | None]:
    """List legacy object IDs from S3 for store_type in File/Thing/Table.

    For each candidate key under {store_type}Data/, fetches object.json
    to surface the real `clazz_name` (so callers can build relay
    GlobalIDs that the node resolver can dispatch to a concrete type).
    Filters out File-prefixed IDs that are >= FIRST_DYNAMO_ID (those
    have been dual-written to DynamoDB and would otherwise duplicate
    entries surfaced via object_identities).

    Returns (items, has_more, last_object_id). Each item dict has
    object_id and object_type keys; object_type is the concrete class
    name (e.g. "RuptureGenerationTask"), not the storage bucket.
    S3 key structure: {store_type}Data/{object_id}/object.json
    """
    if not S3_BUCKET_NAME:
        return [], False, None
    prefix = f"{store_type}Data/"
    s3 = boto3.client("s3", region_name=REGION)

    kwargs: dict[str, Any] = {
        "Bucket": S3_BUCKET_NAME,
        "Prefix": prefix,
        "Delimiter": "/",
        "MaxKeys": limit,
    }
    if after_id:
        kwargs["StartAfter"] = f"{prefix}{after_id}/"
    try:
        resp = s3.list_objects_v2(**kwargs)
    except Exception as exc:
        logger.debug("S3 scan error for %s: %s", store_type, exc)
        return [], False, None

    items = []
    for cp in resp.get("CommonPrefixes", []):
        object_id = cp["Prefix"].rstrip("/").split("/")[-1]
        # File-side dual-write filter: skip post-watermark IDs that are
        # already in DynamoDB (legacy parity, base_data.py:178-183).
        if store_type == "File" and not _is_pre_dynamo_file_id(object_id):
            continue
        clazz_name = _read_clazz_name(s3, S3_BUCKET_NAME, f"{prefix}{object_id}/object.json")
        if not clazz_name:
            # Couldn't read or no clazz_name field — skip rather than
            # surface an identity the node resolver can't dispatch.
            continue
        items.append({"object_id": object_id, "object_type": clazz_name})

    has_more = resp.get("IsTruncated", False)
    last_id = items[-1]["object_id"] if items else None
    return items, has_more, last_id
