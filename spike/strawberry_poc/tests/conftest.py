"""
Test fixtures using DynamoDB Local and Elasticsearch via testcontainers.

Both services start once per session using the official Docker images:
  - amazon/dynamodb-local  — real DynamoDB, supports transact_write_items
  - elasticsearch:7.1.0    — same version as production

DynamoDB tables are created fresh per test module (dropped on teardown) so
modules remain isolated. Elasticsearch is shared across the session; search
tests find whatever is indexed during their own module setup.
"""

import os

import boto3
import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

STAGE = "TEST"
REGION = "us-east-1"
ES_INDEX = "toshi-index-mapped"

os.environ.setdefault("DEPLOYMENT_STAGE", STAGE)
os.environ.setdefault("AWS_DEFAULT_REGION", REGION)
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
# AuthExtension is a no-op when TESTING=1, attaching a synthetic
# current_user with both toshi/read and toshi/write. Tests that need
# to exercise the enforcement path override this with monkeypatch.
os.environ.setdefault("TESTING", "1")

_TABLE_NAMES = [
    f"ToshiThingObject-{STAGE}",
    f"ToshiFileObject-{STAGE}",
    f"ToshiTableObject-{STAGE}",
]
_IDENTITY_TABLE = f"ToshiIdentity-{STAGE}"


def _create_tables(dynamodb):
    for table_name in _TABLE_NAMES:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "object_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "object_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    dynamodb.create_table(
        TableName=_IDENTITY_TABLE,
        KeySchema=[{"AttributeName": "table_name", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "table_name", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _drop_tables(dynamodb):
    for name in _TABLE_NAMES + [_IDENTITY_TABLE]:
        try:
            dynamodb.Table(name).delete()
        except Exception:
            pass


@pytest.fixture(scope="session")
def dynamo_endpoint():
    """Start DynamoDB Local once for the entire test session."""
    container = (
        DockerContainer("amazon/dynamodb-local:latest")
        .with_bind_ports(8000, None)
        .with_command("-jar DynamoDBLocal.jar -inMemory -sharedDb")
    )
    with container as c:
        wait_for_logs(c, "Initializing DynamoDB Local", timeout=30)
        host = c.get_container_host_ip()
        port = c.get_exposed_port(8000)
        yield f"http://{host}:{port}"


@pytest.fixture(scope="session")
def es_endpoint():
    """Start Elasticsearch 7.1.0 once for the entire test session."""
    container = (
        DockerContainer("docker.elastic.co/elasticsearch/elasticsearch:7.1.0")
        .with_bind_ports(9200, None)
        .with_env("discovery.type", "single-node")
        .with_env("ES_JAVA_OPTS", "-Xms256m -Xmx256m")
    )
    with container as c:
        wait_for_logs(c, "started", timeout=60)
        host = c.get_container_host_ip()
        port = c.get_exposed_port(9200)
        endpoint = f"http://{host}:{port}"
        # wait for green/yellow status before yielding
        for _ in range(30):
            try:
                resp = requests.get(f"{endpoint}/_cluster/health", timeout=2)
                if resp.json().get("status") in ("green", "yellow"):
                    break
            except Exception:
                pass
            import time

            time.sleep(1)
        os.environ["ES_ENDPOINT"] = endpoint
        yield endpoint


@pytest.fixture(scope="module")
def dynamodb(dynamo_endpoint):
    """Module-scoped DynamoDB resource — fresh tables per test file."""
    db = boto3.resource(
        "dynamodb",
        endpoint_url=dynamo_endpoint,
        region_name=REGION,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    _create_tables(db)
    yield db
    _drop_tables(db)


@pytest.fixture(scope="module")
def gql_context(dynamodb, es_endpoint):
    return {
        "dynamodb": dynamodb,
        "es_endpoint": es_endpoint,
        "es_index": ES_INDEX,
    }
