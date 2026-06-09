"""
ID allocation and relay GlobalID encoding/decoding.

Replicates the append_uniq + ToshiIdentity pattern from base_data.py,
using raw boto3 instead of PynamoDB (same DynamoDB table, same layout).
"""

import os
import random
from decimal import Decimal

STAGE = os.environ.get("DEPLOYMENT_STAGE", "dev").upper()
FIRST_ID = int(os.environ.get("FIRST_DYNAMO_ID", "100000"))

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def append_uniq(size: int) -> str:
    """Append a 5-char random suffix — matches existing ID format exactly."""
    uniq = "".join(random.choice(_ALPHABET) for _ in range(5))
    return str(size) + uniq


def read_current_id(dynamodb, stage: str = STAGE) -> int:
    """
    Read the current ToshiIdentity counter without incrementing it.
    Seeds the counter to FIRST_ID if it doesn't exist yet.

    _atomic_put() in dynamo.py reads this, then increments + saves the object
    atomically via transact_write_items with a conditional check on the value
    seen here. On concurrent write (TransactionCanceledException), _atomic_put
    retries from this call so a fresh value is always used.
    """
    table = dynamodb.Table(f"ToshiIdentity-{stage}")
    resp = table.get_item(Key={"table_name": stage})
    item = resp.get("Item")
    if item is None:
        table.put_item(Item={"table_name": stage, "object_id": Decimal(FIRST_ID)})
        return FIRST_ID
    return int(item["object_id"])
