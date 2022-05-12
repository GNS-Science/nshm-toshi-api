import datetime as dt
import unittest
import boto3
import json
from io import BytesIO

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb2, mock_s3
from moto.core import patch_client, patch_resource
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.data import data_manager
from graphql_api.schema.search_manager import SearchManager
from graphql_api.schema.custom.common import TaskSubType

from setup_helpers import SetupHelpersMixin

@mock_dynamodb2
@mock_s3
class TestInversionSolution(unittest.TestCase, SetupHelpersMixin):

    def setUp(self):
        self.client = Client(root_schema)

        #S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)

        #Dynamo
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake':'auth'}))

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()


    def test_create_inversion_solution_with_predecessors(self):

        result =  self.create_file("myruptset.zip")
        ruptset_file_id = result['data']['create_file']['file_result']['id']

        isol = self.create_solution_with_predecessor(ruptset_file_id)

        self.assertEqual(isol['predecessors'][0]['depth'], -1)
        self.assertEqual(isol['predecessors'][0]['relationship'], "Parent")


    def create_solution_with_predecessor(self, ruptset_file_id):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!, $produced_by: ID!
                $predecessors: [PredecessorInput])  {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by_id: $produced_by
                  metrics: [{k: "some_metric", v: "20"}]
                  created: "2021-06-11T02:37:26.009506Z"
                  predecessors: $predecessors
                  }
              ) {
                  inversion_solution {
                    id
                    predecessors {
                        id,
                        typename,
                        depth,
                        relationship
                        node {
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

        predecessors = [dict(id=ruptset_file_id, depth=-1)]

        variables = dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID",
            predecessors=predecessors )

        result = self.client.execute(CREATE_QRY, variable_values=variables)

        print(result)
        return result['data']['create_inversion_solution']['inversion_solution']


    def test_get_inversion_solution_with_predecessors(self):

        result =  self.create_file("myruptset.zip")
        ruptset_file_id = result['data']['create_file']['file_result']['id']

        isol = self.create_solution_with_predecessor(ruptset_file_id)

        query = '''
        query inversion_solution_with_predecessors($id: ID!) {
          node(id:$id) {
            __typename
            ... on InversionSolution {
              created
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
        result = self.client.execute(query, variable_values=dict(id=isol['id']))
        print(result)
        node = result['data']['node']
        self.assertEqual(node['predecessors'][0]['depth'], -1)
        self.assertEqual(node['predecessors'][0]['relationship'], "Parent")