import datetime as dt
import unittest

import boto3
import json
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import to_global_id
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking
from setup_helpers import SetupHelpersMixin
from nzshm_common.util import decompress_string


from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.data.thing_data import ThingData
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager


@mock_dynamodb
@mock_s3
class TestOpenquakeHazardTask(unittest.TestCase, SetupHelpersMixin):
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

    def test_create_oq_hazard_task(self):
        haztask = self._build_hazard_task()

        print(haztask)
        hazard_thing = ToshiThingObject.get("100001")
        self.assertEqual(hazard_thing.object_content['clazz_name'], "OpenquakeHazardTask")
        self.assertEqual(json.loads(hazard_thing.object_content['srm_logic_tree']), {'srm': "tree"})
        self.assertEqual(json.loads(hazard_thing.object_content['gmcm_logic_tree']), {'gmcm': "tree"})

    def _build_hazard_task(self):
        return super().build_hazard_task()

    def test_link_tasks(self):
        haztask = self._build_hazard_task() # Thing 100001
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        self.create_gt_relation(self.new_gt, ht_id)  # Thing 100002

        self.assertEqual(
            ToshiThingObject.get("100000").object_content['children'][0],
            {'child_clazz': 'OpenquakeHazardTask', 'child_id': '100001'},
        )

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['parents'][0],
            {'parent_clazz': 'GeneralTask', 'parent_id': '100000'},
        )

    def test_get_openquake_hazard_task_node(self):
        haztask = self._build_hazard_task() # Thing 100001
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
        query openquake_hazard_task($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardTask {
              created
              task_type
              srm_logic_tree
              gmcm_logic_tree
              openquake_config
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

        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta)

        self.assertEqual(haztask['task_type'], "HAZARD")
        self.assertEqual(json.loads(haztask["srm_logic_tree"]), {"srm": "tree"})
        self.assertEqual(json.loads(haztask["gmcm_logic_tree"]), {"gmcm": "tree"})
        self.assertEqual(json.loads(haztask["openquake_config"]), {"openquake": "config"})

    def test_bugfix_148(self):
        '''
        ref https://github.com/GNS-Science/nshm-toshi-api/issues/148
        Source models can return File objects as well as InversionSolutionNrml objects.
        The id for each item should reflect this, but at right now they're always returning the type InversionSolutionNrml.
        '''

        upstream_sid = self.create_source_solution()  # File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid)  # File 100002

        # setup need to create source models both NRML and ordinary File
        nrml_id0 = inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        nrml_1 = self.create_file("bgsesimicity-nrml.zip")  # File 100003
        nrml_id1 = nrml_1['data']['create_file']['file_result']['id']

        archive = self.create_file("config_archive.zip")  # File 100004
        archive_id = archive['data']['create_file']['file_result']['id']

        config = self.create_openquake_config([nrml_id0, nrml_id1], archive_id)  # Thing 100001
        config_id = config['data']['create_openquake_hazard_config']['config']['id']

        haztask = self.create_openquake_hazard_task(config=config_id)  # Thing 100002
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
        self.assertEqual(haztask['config']['source_models'][0]['id'], nrml_id0)
        self.assertEqual(haztask['config']['source_models'][1]['id'], nrml_id1)


    def test_deprecated(self):
        '''
        Assert that we can read deprecated properties
        '''

        upstream_sid = self.create_source_solution()  # File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid)  # File 100002

        # setup need to create source models both NRML and ordinary File
        nrml_id0 = inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']
        nrml_1 = self.create_file("bgsesimicity-nrml.zip")  # File 100003
        nrml_id1 = nrml_1['data']['create_file']['file_result']['id']

        archive = self.create_file("config_archive.zip")  # File 100004
        archive_id = archive['data']['create_file']['file_result']['id']

        config = self.create_openquake_config([nrml_id0, nrml_id1], archive_id)  # Thing 100001
        config_id = config['data']['create_openquake_hazard_config']['config']['id']

        haztask = self.create_openquake_hazard_task(config=config_id)  # Thing 100002
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
        self.assertEqual(haztask['config']['source_models'][0]['id'], nrml_id0)
        self.assertEqual(haztask['config']['source_models'][1]['id'], nrml_id1)


    def test_update_task_with_metrics(self):
        haztask = self._build_hazard_task()
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        things = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        hazsol = things.create(clazz_name='OpenquakeHazardSolution', created=dt.datetime.now(tzutc()))
        # print(hazsol)
        # print(dir(hazsol))
        ohs_id = to_global_id("OpenquakeHazardSolution", hazsol.id)
        executor = "ERCD:sha:the-digest"

        qry = '''
            mutation ($task_id: ID!, $hazard_solution_id: ID!, $executor: String) {
                update_openquake_hazard_task(input: {
                    task_id: $task_id
                    duration: 909,
                    metrics: {k: "rupture_count" v: "20"}
                    hazard_solution: $hazard_solution_id
                    executor: $executor
                })
                {
                    openquake_hazard_task {
                        id
                        duration
                        metrics {k v}
                        hazard_solution {__typename, id}
                        executor
                    }
                }
            }
        '''
        executed = self.client.execute(qry, variable_values=dict(task_id=ht_id, hazard_solution_id=ohs_id, executor=executor))
        print(executed)
        result = executed['data']['update_openquake_hazard_task']['openquake_hazard_task']
        assert result['id'] == ht_id
        assert result['duration'] == 909
        assert result['metrics'][0]['k'] == "rupture_count"
        assert result['metrics'][0]['v'] == "20"
        assert result['hazard_solution']['__typename'] == "OpenquakeHazardSolution"
        assert result['hazard_solution']['id'] == ohs_id
        assert result['executor'] == executor

    def test_update_task_without_hazard_soln(self):
        haztask = self._build_hazard_task()
        ht_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        things = ThingData({}, self._data_manager, ToshiThingObject, self._connection)

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
        assert not (result.get('hazard_solution'))
