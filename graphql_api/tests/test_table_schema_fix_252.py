"""
Test for error 252 where table creation is failing.
"""

import unittest
from unittest import mock

import boto3
import pytest
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

import graphql_api.data  # for mocking
from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiIdentity, ToshiTableObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

CREATE_TABLE = '''
mutation create_table (
    $rows: [[String]]!, $object_id: ID!, $table_name: String!, $headers: [String]!,
    $column_types: [RowItemType]!, $created: DateTime!, $table_type: TableType!,
    $dimensions: [KeyValueListPairInput]!
) {
    create_table(input: {
    name: $table_name
    created: $created
    table_type: $table_type
    dimensions: $dimensions
    object_id: $object_id
    column_headers: $headers
    column_types: $column_types
    rows: $rows
    })
    {
    table {
        id
    }
    }
}'''

INPUT_VARIABLES = {
    'headers': ['series', 'series_name', 'X', 'Y'],
    'object_id': 'SW52ZXJzaW9uU29sdXRpb246MTAxOTY2',
    'rows': [['0', 'foo', '1.0', '2.0'], ['1', 'bar', '1.5', '2.5']],
    'column_types': ['integer', 'string', 'double', 'double'],
    'table_name': 'Inversion Solution MFD table',
    'created': '2025-08-06T23:32:58.526823Z',
    'table_type': 'MFD_CURVES',
    'dimensions': [],
}


class IncrId:
    next_id = -1

    def get_next_id(self, *args):
        self.next_id += 1
        return str(self.next_id) + 'RANDM'


def json_dumps_mock(obj):
    raise RuntimeError(str(obj))
    return None


@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
class TestFailingMutation(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', IncrId().get_next_id)
    def test_create_252_exmple_table(self):

        # this query comes from:
        # nzshm-runzi/runzi/automation/scaling/toshi_api/toshi_api.py
        # https://github.com/GNS-Science/nzshm-runzi/blob/8c390a34d3a803fd357846aadfce21b891c9d299/runzi/automation/scaling/toshi_api/toshi_api.py#L250C1-L274C60
        #
        # which fails with error message:
        # {'message': 'Object of type EnumMeta is not JSON serializable', 'locations': [{'line': 2, 'column': 3}], 'path': ['create_table']}

        print(CREATE_TABLE)

        result = self.client.execute(CREATE_TABLE, variable_values=INPUT_VARIABLES)
        print(result)
        assert result['data']['create_table']['table']['id'] == 'VGFibGU6MFJBTkRN'


@mock_s3
@mock_dynamodb
class TestFailingMutationWithMockedServices(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        # migrate()

        self._s3_conn = boto3.resource('s3', region_name=REGION)
        self._s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3_conn.Bucket(S3_BUCKET_NAME)
        self._connection = Connection(region=REGION)

        ToshiTableObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))

    def test_create_one_table(self):

        print(CREATE_TABLE)

        result = self.client.execute(CREATE_TABLE, variable_values=INPUT_VARIABLES)
        print(result)
        assert result['data']['create_table']['table']['id'] == 'VGFibGU6MTAwMDAw'

    @mock.patch('graphql_api.data.base_data.json_serialised', json_dumps_mock)
    def test_new_logging_exception_handing(self):
        print(CREATE_TABLE)
        result = self.client.execute(CREATE_TABLE, variable_values=INPUT_VARIABLES)
        print(result['errors'])
        assert result['errors'][0]['message'].find("This object cannot be persisted to a PynamoDB.Model") != -1
