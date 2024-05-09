import pytest
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id

import graphql_api.data
import graphql_api.data.base_data
from graphql_api.schema import root_schema
from graphql_api.schema.object_identities import ObjectIdentity


@pytest.fixture(scope="module")
def graphene_client():
    yield Client(root_schema)


class MockS3Client:
    def generate_presigned_url(self, key, Params, ExpiresIn):
        return "ABCD"


# custom mock for graphql_api.data.BaseDynamoDBData_read_obect
mock_db_read = lambda _self, _id: {"id": _id, "clazz_name": "File", "file_size": 123, "file_name": "My fake file"}


@pytest.fixture
def mock_dbdata(monkeypatch):
    """graphql_api.data.BaseDynamoDBData._read_object"""
    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, "_read_object", mock_db_read)
    monkeypatch.setattr(graphql_api.data.base_data.BaseData, "s3_client", MockS3Client())


def test_bug_squashed_coz_we_called_s3_client(graphene_client, mock_dbdata):
    node_id = to_global_id("File", '1001')
    QRY = (
        """
        query {
		  node(id:"%s") {
		    ... on File {
		      file_url
		      file_name
		      file_size
		    }
		  }
		}
    """
        % node_id
    )

    print(QRY)
    result = graphene_client.execute(QRY)  # , variable_values=dict(created=dt.datetime.now(tzutc())))
    print(result)
    assert result['data']['node']['file_name'] == "My fake file"
    assert result['data']['node']['file_size'] == 123
    assert result['data']['node']['file_url'] == "ABCD"
