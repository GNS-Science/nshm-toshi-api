"""
For API data management we want a way to iterate all the objects in the store.

 - test the graphql endpoint

 - note we're goin to use the pytest (not unit-test) approach

"""
import pytest
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id

import graphql_api.data
from graphql_api.schema import root_schema
from graphql_api.schema.object_identities import ObjectIdentity


@pytest.fixture(scope="module")
def graphene_client():
    yield Client(root_schema)


# mock class for graphql_api.data.BaseDynamoDBData
class MockDBdata:
    next_id = -1

    def get_next_id(self, *args):
        self.next_id += 1
        return self.next_id

    def get_all_gt(self, object_type, limit, *args, **kwargs):
        if object_type in ["GeneralTask"]:
            for n in range(limit):
                yield ObjectIdentity(
                    object_type="GeneralTask", object_id=str(n), node_id=to_global_id("GeneralTask", str(n))
                )


# custom mock for graphql_api.data.BaseDynamoDBData_read_obect
mock_db_read = lambda _self, _id: {
    "id": _id,
    "clazz_name": "GeneralTask",
}


def mock_get_all_s3_paginated(self, limit, after):
    for n in range(limit):
        yield ObjectIdentity(object_type="GeneralTask", object_id=str(n), node_id=to_global_id("GeneralTask", str(n)))


@pytest.fixture
def mock_dbdata(monkeypatch):
    """graphql_api.data.BaseDynamoDBData._read_object"""
    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, "_read_object", mock_db_read)
    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, "get_all", MockDBdata().get_all_gt)
    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, "get_next_id", MockDBdata().get_next_id)
    monkeypatch.setattr(graphql_api.data.BaseData, "get_all_s3_paginated", mock_get_all_s3_paginated)


def test_iterate_object_identities_resolver(graphene_client, mock_dbdata):
    """Test fgor modern DynamoDB objects"""
    QRY = """
        query {
            object_identities(
                object_type: "GeneralTask"
                first: 3
            )
            {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                    cursor
                    node {
                        __typename

                        object_type
                        object_id
                        node_id
                        # clazz_name

                    }
                }
            }
        }
    """

    result = graphene_client.execute(QRY)  # , variable_values=dict(created=dt.datetime.now(tzutc())))
    print(result)
    assert len(result['data']['object_identities']['edges']) == 3
    assert result['data']['object_identities']['edges'][0]['node']['node_id'] == to_global_id("GeneralTask", "0")


def test_iterate_legacy_object_identities_resolver(graphene_client, mock_dbdata):
    """Test fgor modern DynamoDB objects"""
    QRY = """
        query {
            legacy_object_identities(
                store_type: "Thing"
                first: 3
            )
            {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                    cursor
                    node {
                        __typename
                        object_type
                        object_id
                        node_id
                        # clazz_name

                    }
                }
            }
        }
    """

    result = graphene_client.execute(QRY)  # , variable_values=dict(created=dt.datetime.now(tzutc())))
    print(result)
    assert len(result['data']['legacy_object_identities']['edges']) == 3
    assert result['data']['legacy_object_identities']['edges'][0]['node']['node_id'] == to_global_id("GeneralTask", "0")
