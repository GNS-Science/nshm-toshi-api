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
                    state: UNDEFINED
                    result: UNDEFINED

                    arguments: [
                        { k:"max_jump_distance" v: "55.5" }
                        { k:"max_sub_section_length" v: "2" }
                        { k:"max_cumulative_azimuth" v: "590" }
                        { k:"min_sub_sections_per_parent" v: "2" }
                        { k:"permutation_strategy" v: "DOWNDIP" }
                    ]

                    environment: [
                        { k:"gitref_opensha_ucerf3" v: "ABC"}
                        { k:"gitref_opensha_commons" v: "ABC"}
                        { k:"gitref_opensha_core" v: "ABC"}
                        { k:"nshm_nz_opensha" v: "ABC"}
                        { k:"host" v:"tryharder-ubuntu"}
                        { k:"JAVA" v:"-Xmx24G"  }
                    ]
                  }
              )
              {
                ok
                openquake_hazard_task { id, config { id }, created, arguments {k v}}
              }
            }'''

        variables = dict(config=config, created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result


    def test_create_oq_hazard_task(self):

        haztask = self._build_hazard_task()

        print (haztask)
        self.assertEqual(
            ToshiThingObject.get("100002").object_content['clazz_name'], "OpenquakeHazardTask")


    def _build_hazard_task(self):

        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        archive = self.create_file("config_archive.zip") #File 100003
        archive_id = archive['data']['create_file']['file_result']['id']

        config = self.create_openquake_config([nrml_id], archive_id) #Thing 100001
        config_id = config['data']['create_openquake_hazard_config']['config']['id']

        haztask = self.create_openquake_hazard_task(config_id) #Thing 100002
        return haztask


    def test_link_tasks(self):
        haztask = self._build_hazard_task()
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        self.create_gt_relation(self.new_gt, ht_id) #Thing 100003

        self.assertEqual(
            ToshiThingObject.get("100000").object_content['children'][0],
            {'child_clazz': 'OpenquakeHazardTask', 'child_id': '100002'})

        self.assertEqual(
            ToshiThingObject.get("100002").object_content['parents'][0],
            {'parent_clazz': 'GeneralTask', 'parent_id': '100000'})


    def test_get_openquake_hazard_task_node(self):

        haztask = self._build_hazard_task()
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
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta )

        self.assertEqual(haztask['config']['source_models'][0]['file_name'],
            "alineortwo.zip")
        self.assertEqual(haztask['config']['source_models'][0]['source_solution']['file_name'],
            "MyInversion.zip")

    def test_update_task_with_metrics(self):

        haztask = self._build_hazard_task()
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        qry = '''
            mutation ($task_id: ID!) {
                update_openquake_hazard_task(input: {
                    task_id: $task_id
                    duration: 909,
                    metrics: {k: "rupture_count" v: "20"}
                })
                {
                    openquake_hazard_task {
                        id
                        duration
                        metrics {k v}
                    }
                }
            }
        '''
        executed = self.client.execute(qry, variable_values=dict(task_id=ht_id))
        print(executed)
        result = executed['data']['update_openquake_hazard_task']['openquake_hazard_task']
        assert result['id'] == ht_id
        assert result['duration'] == 909
        assert result['metrics'][0]['k'] == "rupture_count"
        assert result['metrics'][0]['v'] == "20"



