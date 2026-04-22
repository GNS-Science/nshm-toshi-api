"""
Test fixtures — mirrors the pattern in graphql_api/tests/conftest.py.

Uses moto to mock DynamoDB. Tests call schema.execute_sync() directly,
bypassing HTTP so they're fast and don't need a running server.
"""
import os
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

STAGE = "test"
REGION = "us-east-1"

# Must be set before importing anything that reads DEPLOYMENT_STAGE at module load
os.environ.setdefault("DEPLOYMENT_STAGE", STAGE)
os.environ.setdefault("AWS_DEFAULT_REGION", REGION)
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")


def create_tables(dynamodb):
    """Create the three Toshi DynamoDB tables in the moto mock."""
    for table_name in [
        f"ToshiThingObject-{STAGE}",
        f"ToshiFileObject-{STAGE}",
        f"ToshiTableObject-{STAGE}",
    ]:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "object_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "object_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    dynamodb.create_table(
        TableName=f"ToshiIdentity-{STAGE}",
        KeySchema=[{"AttributeName": "table_name", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "table_name", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture(scope="module")
def dynamodb():
    """Module-scoped moto DynamoDB resource with all tables created."""
    with mock_aws():
        db = boto3.resource("dynamodb", region_name=REGION)
        create_tables(db)
        yield db


@pytest.fixture(scope="module")
def gql_context(dynamodb):
    """GraphQL context dict injected into schema.execute_sync() calls."""
    return {"dynamodb": dynamodb}
