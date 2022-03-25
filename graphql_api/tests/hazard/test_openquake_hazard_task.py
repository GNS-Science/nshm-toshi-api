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

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()

    def create_openquake_hazard_task(self, config):
        """test helper"""
        query = '''
            mutation ($created: DateTime!, $config: ID!) {
              create_openquake_hazard_task(
                  input: {
                      config: $config
                      created: $created
                  }
              )
              {
                ok
                openquake_hazard_task { id, config { id }, created}
              }
            }'''

        variables = dict(config=config, created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result


    def test_create_oq_hazard_task(self):

        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        config = self.create_openquake_config([nrml_id]) #Thing 100001
        config_id = config['data']['create_openquake_hazard_config']['config']['id'] #Thing 100002

        haztask = self.create_openquake_hazard_task(config_id)

        print (haztask)
        self.assertEqual(
            ToshiThingObject.get("100002").object_content['clazz_name'], "OpenquakeHazardTask")


    def test_link_tasks(self):
        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        config = self.create_openquake_config([nrml_id]) #Thing 100001
        config_id = config['data']['create_openquake_hazard_config']['config']['id']

        haztask = self.create_openquake_hazard_task(config_id) #Thing 100002
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        self.create_gt_relation(self.new_gt, ht_id) #Thing 100003

        self.assertEqual(
            ToshiThingObject.get("100000").object_content['children'][0],
            {'child_clazz': 'OpenquakeHazardTask', 'child_id': '100002'})

        self.assertEqual(
            ToshiThingObject.get("100002").object_content['parents'][0],
            {'parent_clazz': 'GeneralTask', 'parent_id': '100000'})


    def test_get_openquake_hazard_task_node(self):

        upstream_sid = self.create_source_solution()
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002

        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        config = self.create_openquake_config([nrml_id])

        config_id = config['data']['create_openquake_hazard_config']['config']['id']
        haztask = self.create_openquake_hazard_task(config_id)
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
        query openquake_hazard_task($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardTask {
              created
              config {
                id
                created
                source_models {
                    id
                    file_name
                    source_solution {
                        id
                        file_name
                    }
                }
              }
            }
          }
        }
        '''

        result = self.client.execute(query, variable_values=dict(id=ht_id))
        print(result)
        haztask = result['data']['node']

        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(microseconds=10000)
        self.assertTrue(delta < max_delta )

        self.assertEqual(haztask['config']['source_models'][0]['file_name'],
            "alineortwo.zip")
        self.assertEqual(haztask['config']['source_models'][0]['source_solution']['file_name'],
            "MyInversion.zip")

    @unittest.skip('WIP')
    def test_create_opensha_nrml_from_solution(self):
        at_id = self.create_automation_task("SOLUTION_TO_NRML")
        upstream_sid = self.create_source_solution()
        result = self.create_inversion_solution_nrml(upstream_sid)

        ss =  result['data']['create_inversion_solution_nrml']['inversion_solution_nrml']

        self.assertEqual(ss['source_solution']['id'], upstream_sid)

        print(ToshiFileObject.get("100002").object_content)

        #object ID is stored internally as an INT
        self.assertEqual(ToshiFileObject.get("100002").object_content['id'], int(from_global_id(ss['id'])[1]))





