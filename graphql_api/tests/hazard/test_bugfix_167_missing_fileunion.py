import unittest

import boto3
from graphene.test import Client

# from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb, mock_s3

# from moto.core import patch_client, patch_resource
from pynamodb.connection.base import Connection  # for mocking
from setup_helpers import SetupHelpersMixin

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.custom.common import AggregationFn
from graphql_api.schema.search_manager import SearchManager


@mock_dynamodb
@mock_s3
class TestAutomationTaskFileUnion(unittest.TestCase, SetupHelpersMixin):
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

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()
        self.common_ruptset_id = self.create_file("myruptset.zip", self.source_solution)['data']['create_file'][
            'file_result'
        ]['id']

    def test_get_aggregate_solution_from_automation_task(self):
        at_id = self.create_automation_task("AGGREGATE_SOLUTION")
        upstream_sid = self.create_source_solution()
        as_result = self.create_aggregate_solution(
            [upstream_sid], at_id, AggregationFn.MEAN.name, self.common_ruptset_id
        )
        file_id = as_result['data']['create_aggregate_inversion_solution']['solution']['id']

        # query to link the aggregate_solution file with the AutomationTask
        query0 = '''
        mutation create_file_relation(
            $thing_id:ID!
            $file_id:ID!
            $role:FileRole!) {
              create_file_relation(
                file_id:$file_id
                thing_id:$thing_id
                role:$role
              )
            {
              ok
            }
        }'''

        # print(f'parent_id={at_id}, file_id={file_id}')
        # print()

        executed = self.client.execute(query0, variable_values=dict(thing_id=at_id, file_id=file_id, role='WRITE'))
        print(executed)

        query = """
            query get_automation_task($id: ID!) {
              node(id: $id) {
                id
                ... on AutomationTask {
                  id
                  model_type
                  files {
                    total_count
                    edges {

                      node {
                        role
                        file {
                          __typename
                          ... on Node {
                            id
                          }
                          ... on FileInterface {
                            file_name
                            #file_url
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
        """

        result = self.client.execute(query, variable_values=dict(id=at_id))
        print(result)

        node = result['data']['node']
        files = node['files']['edges']
        print(files)

        self.assertEqual(files[0]['node']['file']['id'], file_id)
