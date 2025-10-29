import unittest

import boto3
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking
from setup_helpers import SetupHelpersMixin

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager


@mock_dynamodb
@mock_s3
class TestFile(unittest.TestCase, SetupHelpersMixin):
    def setUp(self):
        self.client = Client(root_schema)

        # S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)

        # Dynamo
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()

    def test_create_file_with_predecessors(self):
        ssid = self.source_solution
        result = self.create_file("myruptset.zip", ssid)
        _file = result['data']['create_file']['file_result']

        self.assertEqual(_file['predecessors'][0]['depth'], -1)
        self.assertEqual(_file['predecessors'][0]['relationship'], "Parent")
        self.assertEqual(_file['predecessors'][0]['id'], ssid)
        return _file

    def test_get_file_with_predecessors(self):
        ssid = self.source_solution
        result = self.create_file("myruptset.zip", ssid)
        _file = result['data']['create_file']['file_result']

        query = '''
        query file_with_predecessors($id: ID!) {
          node(id:$id) {
            ... on FileInterface {
                file_name
            }
            ... on PredecessorsInterface {
                predecessors {
                    id,
                    typename,
                    depth,
                    relationship
                    node {
                        __typename
                        ... on FileInterface {
                            meta {k v}
                            file_name
                        }
                    }
                }
            }

          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=_file['id']))
        print(result)
        node = result['data']['node']
        self.assertEqual(node['predecessors'][0]['depth'], -1)
        self.assertEqual(node['predecessors'][0]['relationship'], "Parent")
        self.assertEqual(node['predecessors'][0]['id'], ssid)
