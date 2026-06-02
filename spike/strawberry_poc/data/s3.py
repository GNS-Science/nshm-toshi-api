"""S3 presigned URL helper — download URLs for file objects."""

import os

import boto3

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
