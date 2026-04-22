"""
ID allocation and relay GlobalID encoding/decoding.

Replicates the append_uniq + ToshiIdentity pattern from base_data.py,
using raw boto3 instead of PynamoDB (same DynamoDB table, same layout).
"""
import os
import random
from decimal import Decimal

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

STAGE = os.environ.get("DEPLOYMENT_STAGE", "dev")
FIRST_ID = int(os.environ.get("FIRST_DYNAMO_ID", "100000"))

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def append_uniq(size: int) -> str:
    """Append a 5-char random suffix — matches existing ID format exactly."""
    uniq = "".join(random.choice(_ALPHABET) for _ in range(5))
    return str(size) + uniq


def next_id(dynamodb, stage: str = STAGE) -> str:
    """
    Atomically increment ToshiIdentity counter and return new object_id string.

    Uses boto3 conditional update instead of PynamoDB VersionAttribute —
    same semantics, no ORM required.
    """
    table = dynamodb.Table(f"ToshiIdentity-{stage}")
    try:
        resp = table.update_item(
            Key={"table_name": stage},
            UpdateExpression="SET object_id = object_id + :inc",
            ConditionExpression=Attr("table_name").exists(),
            ExpressionAttributeValues={":inc": Decimal(1)},
            ReturnValues="UPDATED_NEW",
        )
        return append_uniq(int(resp["Attributes"]["object_id"]))
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # First allocation: seed the counter
            table.put_item(Item={"table_name": stage, "object_id": Decimal(FIRST_ID)})
            return append_uniq(FIRST_ID)
        raise
