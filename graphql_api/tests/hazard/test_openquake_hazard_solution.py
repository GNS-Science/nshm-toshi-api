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
class TestOpenquakeHazardSolution(unittest.TestCase, SetupHelpersMixin):

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

    def test_openquake_hazard_solution(self):

        task_id = to_global_id("AutomationTask", "100001")
        hazout  = self.create_openquake_hazard_solution(task_id)

        self.assertEqual(
            ToshiFileObject.get("100000").object_content['id'], 100000 )

    def test_get_openquake_hazard_solution_node(self):

        task_id = to_global_id("AutomationTask", "100001")
        result  = self.create_openquake_hazard_solution(task_id)
        hazout_id =  result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

        query = '''
        query get_scaled_solution($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardSolution {
              created
            }
          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=hazout_id))
        print(result)

        delta = dt.datetime.utcnow() - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta )

    def create_openquake_hazard_solution(self, task_id):
        """test helper"""
        query = '''
            mutation ($produced_by: ID!, $digest: String!, $file_name: String!, $file_size: Int!, $created: DateTime!) {
              create_openquake_hazard_solution(
                  input: {
                      produced_by: $produced_by
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                  }
              )
              {
                ok
                openquake_hazard_solution { id, file_name, file_size, md5_digest, post_url, produced_by { id }}
              }
            }'''

        from hashlib import sha256, md5
        filedata = BytesIO("not_really zip, but close enough".encode())
        digest = sha256(filedata.read()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!

        variables = dict(produced_by=task_id, file=filedata, digest=digest, file_name="alineortwo.zip", file_size=size)
        variables['created'] = dt.datetime.utcnow().isoformat()
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result


