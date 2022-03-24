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
class TestOpenquakeHazardTask(unittest.TestCase, SetupHelpersMixin):

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

        self.new_gt = self.create_general_task() #Thing 100000
        self.source_solution = self.create_source_solution() #File 100000


    def create_openquake_config(self, sources):
        """test helper"""
        query = '''
            mutation ($created: DateTime!, $sources: [ID!]) {
              create_openquake_hazard_config(
                  input: {
                      created: $created
                      source_models: $sources
                  }
              )
              {
                ok
                config { id, created, source_models { id } }
              }
            }'''

        variables = dict(sources=sources)
        variables['created'] = dt.datetime.now(tzutc()).isoformat()
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result

    def test_create_a_hazard_config(self):
        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']

        result = self.create_openquake_config([nrml_id]) #Thing 100001

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['clazz_name'], 'OpenquakeHazardConfig' )

        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['create_openquake_hazard_config']['config']['created'])
        max_delta = dt.timedelta(microseconds=10000)
        self.assertTrue(delta < max_delta )

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['source_models'][0], nrml_id)

    def test_get_hazard_config_node(self):

        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        config = self.create_openquake_config([nrml_id]) #Thing 100001

        hc_id =  config['data']['create_openquake_hazard_config']['config']['id']
        print(f"hcid {hc_id}")

        query = '''
        query get_openquake_hazard_config($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardConfig{
              created
              source_models {
                id
                # source_solution {
                #     created
                # }
              }
            }
          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=hc_id))
        print(result)
        #assert 0
        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(microseconds=10000)
        self.assertTrue(delta < max_delta )
