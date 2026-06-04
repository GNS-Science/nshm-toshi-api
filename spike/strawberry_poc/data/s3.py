"""S3 helpers — presigned download URLs and legacy object enumeration."""

import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
REGION = os.environ.get("REGION", "ap-southeast-2")
_URL_TTL = int(os.environ.get("URL_DEFAULT_TTL", "3600"))


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


def scan_s3_paginated(
    store_type: str,
    limit: int = 5,
    after_id: str | None = None,
) -> tuple[list[dict], bool, str | None]:
    """List legacy object IDs from S3 for store_type in File/Thing/Table.

    Returns (items, has_more, last_object_id).  Each item dict has object_id
    and object_type keys; clazz_name is not available without fetching the JSON.
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
        items.append({"object_id": object_id, "object_type": store_type})
    has_more = resp.get("IsTruncated", False)
    last_id = items[-1]["object_id"] if items else None
    return items, has_more, last_id
