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
class TestScaling(unittest.TestCase, SetupHelpersMixin):

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

    def test_create_and_scaled_solution_task(self):
        at_id = self.create_automation_task("SCALE_SOLUTION")

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['task_type'],
            TaskSubType.SCALE_SOLUTION.value )

    def test_create_and_link_tasks(self):
        at_id = self.create_automation_task("SCALE_SOLUTION")
        self.create_gt_relation(self.new_gt, at_id)

        self.assertEqual(
            ToshiThingObject.get("100000").object_content['children'][0],
            {'child_clazz': 'AutomationTask', 'child_id': '100001'})

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['parents'][0],
            {'parent_clazz': 'GeneralTask', 'parent_id': '100000'})

    # @unittest.skip('TODO')
    def test_create_scaled_solution(self):
        at_id = self.create_automation_task("SCALE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_scaled_solution(upstream_sid)

        ss =  result['data']['create_scaled_inversion_solution']['solution']

        self.assertEqual(ss['source_solution']['id'], upstream_sid)

        print(ToshiFileObject.get("100002").object_content)

        #object ID is stored internally as an INT
        self.assertEqual(ToshiFileObject.get("100002").object_content['id'], int(from_global_id(ss['id'])[1]))


    def test_get_scaled_solution_node(self):

        at_id = self.create_automation_task("SCALE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_scaled_solution(upstream_sid)

        ss_id =  result['data']['create_scaled_inversion_solution']['solution']['id']

        query = '''
        query get_scaled_solution($id: ID!) {
          node(id:$id) {
            __typename
            ... on ScaledInversionSolution {
              created
            }
          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=ss_id))
        print(result)

        delta = dt.datetime.utcnow() - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(microseconds=10000)
        self.assertTrue(delta < max_delta )


    def create_scaled_solution(self, upstream_sid):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $digest: String!, $file_name: String!, $file_size: Int!, $created: DateTime!) {
              create_scaled_inversion_solution(
                  input: {
                      source_solution: $source_solution
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                  }
              )
              {
                ok
                solution { id, file_name, file_size, md5_digest, post_url, source_solution { id }}
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(source_solution=upstream_sid, file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size)
        variables['created'] = dt.datetime.utcnow().isoformat()
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result


