import datetime as dt
import unittest
import boto3
import json
from io import BytesIO
from unittest import mock
from dateutil.tz import tzutc

from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb, mock_s3
from moto.core import patch_client, patch_resource
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.data import data_manager
from graphql_api.schema.search_manager import SearchManager
from graphql_api.schema.custom.common import TaskSubType
from graphql_api.data.thing_data import ThingData

from setup_helpers import SetupHelpersMixin

import graphql_api.data # for mocking

MOCK_LEGACY_HAZARD_TASK = lambda _self, _id: {'id': _id,
    'created': '2023-03-24T01:52:07.407832+00:00',
    'files': None, 'parents': None, 'children': None, 'result': 'undefined', 'state': 'undefined', 'duration': None,
    'arguments': [{'k': 'max_jump_distance', 'v': '55.5'}, {'k': 'max_sub_section_length', 'v': '2'}, {'k': 'max_cumulative_azimuth', 'v': '590'}, {'k': 'min_sub_sections_per_parent', 'v': '2'}, {'k': 'permutation_strategy', 'v': 'DOWNDIP'}], 'environment': [{'k': 'gitref_opensha_ucerf3', 'v': 'ABC'}, {'k': 'gitref_opensha_commons', 'v': 'ABC'}, {'k': 'gitref_opensha_core', 'v': 'ABC'}, {'k': 'nshm_nz_opensha', 'v': 'ABC'}, {'k': 'host', 'v': 'tryharder-ubuntu'}, {'k': 'JAVA', 'v': '-Xmx24G'}],
    'metrics': None, 'config': 'T3BlbnF1YWtlSGF6YXJkQ29uZmlnOjEwMDAwMQ==', 'hazard_solution': None, 'model_type': 'composite',
    'clazz_name': 'OpenquakeHazardTask'}



@mock_dynamodb
@mock_s3
class TestOpenquakeHazardDisaggTask(unittest.TestCase, SetupHelpersMixin):

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


    def test_create_oq_hazard_disagg_task(self):

        haztask = self._build_hazard_task()

        print (haztask)
        self.assertEqual(
            ToshiThingObject.get("100002").object_content['clazz_name'], "OpenquakeHazardTask")
        self.assertEqual(
            ToshiThingObject.get("100002").object_content['task_type'], "disagg")



    def _build_hazard_task(self):
        return super().build_hazard_task(disagg=True)

    # def test_link_tasks(self):
    #     haztask = self._build_hazard_task()
    #     ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

    #     self.create_gt_relation(self.new_gt, ht_id) #Thing 100003

    #     self.assertEqual(
    #         ToshiThingObject.get("100000").object_content['children'][0],
    #         {'child_clazz': 'OpenquakeHazardTask', 'child_id': '100002'})

    #     self.assertEqual(
    #         ToshiThingObject.get("100002").object_content['parents'][0],
    #         {'parent_clazz': 'GeneralTask', 'parent_id': '100000'})


    def test_get_openquake_hazard_disagg_task_node(self):

        haztask = self._build_hazard_task()
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
        query openquake_hazard_task($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardTask {
              created
              task_type
              config {
                id
                created
                source_models {
                    ... on Node { id }
                    ... on FileInterface { file_name }
                    ... on InversionSolutionNrml {
                        source_solution {
                            ... on Node{ id }
                            ... on FileInterface { file_name }
                        }
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

        self.assertEqual(haztask['task_type'], "DISAGG")

@mock_dynamodb
@mock_s3
class TestOpenquakeLegacyHazardDisaggTask(unittest.TestCase):

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


    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', MOCK_LEGACY_HAZARD_TASK)
    def test_legacy_hazard_task_has_default_task_type(self):

        ht_id = to_global_id("OpenquakeHazardTask", "10002")

        query = '''
        query openquake_hazard_task($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardTask {
              created
              task_type
            }
          }
        }
        '''

        result = self.client.execute(query, variable_values=dict(id=ht_id))
        print(result)
        haztask = result['data']['node']
        self.assertTrue(haztask['created'])
        self.assertEqual(haztask['task_type'], "UNDEFINED")


    # def test_update_task_with_metrics(self):

    #     haztask = self._build_hazard_task()
    #     ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']


    #     things = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
    #     hazsol = things.create(clazz_name='OpenquakeHazardSolution', created=dt.datetime.now(tzutc()))
    #     # print(hazsol)
    #     # print(dir(hazsol))
    #     ohs_id = to_global_id("OpenquakeHazardSolution", hazsol.id)

    #     qry = '''
    #         mutation ($task_id: ID!, $hazard_solution_id: ID!) {
    #             update_openquake_hazard_task(input: {
    #                 task_id: $task_id
    #                 duration: 909,
    #                 metrics: {k: "rupture_count" v: "20"}
    #                 hazard_solution: $hazard_solution_id
    #             })
    #             {
    #                 openquake_hazard_task {
    #                     id
    #                     duration
    #                     metrics {k v}
    #                     hazard_solution {__typename, id}
    #                 }
    #             }
    #         }
    #     '''
    #     executed = self.client.execute(qry, variable_values=dict(task_id=ht_id, hazard_solution_id=ohs_id))
    #     print(executed)
    #     result = executed['data']['update_openquake_hazard_task']['openquake_hazard_task']
    #     assert result['id'] == ht_id
    #     assert result['duration'] == 909
    #     assert result['metrics'][0]['k'] == "rupture_count"
    #     assert result['metrics'][0]['v'] == "20"
    #     assert result['hazard_solution']['__typename'] == "OpenquakeHazardSolution"
    #     assert result['hazard_solution']['id'] == ohs_id

    
    # def test_update_task_without_hazard_soln(self):

    #     haztask = self._build_hazard_task()
    #     ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

    #     things = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
    #     hazsol = things.create(clazz_name='OpenquakeHazardSolution', created=dt.datetime.now(tzutc()))

    #     qry = '''
    #         mutation ($task_id: ID!) {
    #             update_openquake_hazard_task(input: {
    #                 task_id: $task_id
    #                 duration: 909,
    #                 metrics: {k: "rupture_count" v: "20"}
    #             })
    #             {
    #                 openquake_hazard_task {
    #                     id
    #                     duration
    #                     metrics {k v}
    #                 }
    #             }
    #         }
    #     '''
    #     executed = self.client.execute(qry, variable_values=dict(task_id=ht_id))
    #     print(executed)
    #     result = executed['data']['update_openquake_hazard_task']['openquake_hazard_task']
    #     assert result['id'] == ht_id
    #     assert result['duration'] == 909
    #     assert result['metrics'][0]['k'] == "rupture_count"
    #     assert result['metrics'][0]['v'] == "20"
    #     assert not (result.get('hazard_solution'))

    

