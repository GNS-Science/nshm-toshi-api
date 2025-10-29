import datetime as dt
import unittest

import boto3
from dateutil.tz import tzutc
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
class TestOpenquakeHazardSolution(unittest.TestCase, SetupHelpersMixin):
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

    def test_create_openquake_hazard_solution(self):
        upstream_sid = self.create_source_solution()  # File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid)  # File 100002
        nrml_id = inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']

        archive = self.create_file("config_archive.zip")  # File 100003
        archive_id = archive['data']['create_file']['file_result']['id']
        result = self.create_openquake_config([nrml_id], archive_id)  # Thing 100000

        csv_archive = self.create_file("csv_archive.zip")  # File 100004
        csv_archive_id = csv_archive['data']['create_file']['file_result']['id']
        # self.assertEqual(
        #     ToshiThingObject.get("100000").object_content['clazz_name'], 'OpenquakeHazardConfig' )

        haztask = self.build_hazard_task()
        haztask_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
            mutation ($created: DateTime!, $csv_archive_id: ID!, $produced_by:ID!, $predecessors: [PredecessorInput]) {
              create_openquake_hazard_solution(
                  input: {
                      created: $created
                      csv_archive: $csv_archive_id
                      #hdf5_archive: $hdf5_archive_id
                      produced_by: $produced_by
                      predecessors: $predecessors
                  }
              )
              {
                ok
                openquake_hazard_solution { id
                    csv_archive { id, file_name }
                    produced_by { id }
                }
              }
            }'''

        predecessors = [dict(id=nrml_id, depth=-1)]
        variables = dict(
            created=dt.datetime.now(tzutc()).isoformat(),
            csv_archive_id=csv_archive_id,
            produced_by=haztask_id,
            predecessors=predecessors,
        )

        result = self.client.execute(query, variable_values=variables)
        # print(result)
        oqs = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']
        self.assertEqual(oqs['csv_archive']['file_name'], "csv_archive.zip")
        self.assertEqual(oqs['produced_by']['id'], haztask_id)
        return result

    def test_create_openquake_hazard_solution_deprecated(self):
        '''
        Assert that we can still read deprecated properties
        '''
        upstream_sid = self.create_source_solution()  # File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid)  # File 100002
        nrml_id = inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']

        archive = self.create_file("config_archive.zip")  # File 100003
        archive_id = archive['data']['create_file']['file_result']['id']
        config = self.create_openquake_config([nrml_id], archive_id)  # Thing 100000
        config_id = config['data']['create_openquake_hazard_config']['config']['id']

        csv_archive = self.create_file("csv_archive.zip")  # File 100004
        csv_archive_id = csv_archive['data']['create_file']['file_result']['id']

        haztask = self.build_hazard_task()
        haztask_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
            mutation ($created: DateTime!, $csv_archive_id: ID!, $produced_by:ID!, $config:ID, $modified_config:ID) {
              create_openquake_hazard_solution(
                  input: {
                      created: $created
                      csv_archive: $csv_archive_id
                      #hdf5_archive: $hdf5_archive_id
                      produced_by: $produced_by
                      config: $config
                      modified_config: $modified_config
                  }
              )
              {
                ok
                openquake_hazard_solution { id
                    csv_archive { id, file_name }
                    produced_by { id }
                }
              }
            }'''

        variables = dict(
            created=dt.datetime.now(tzutc()).isoformat(),
            csv_archive_id=csv_archive_id,
            produced_by=haztask_id,
            config=config_id,
            modified_config=archive_id,
        )

        result = self.client.execute(query, variable_values=variables)
        print(result)
        oqs_id = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

        query = '''
        query get_solution($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardSolution {
                config {
                id
                }
                modified_config {
                id
                }
            }
          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=oqs_id))
        print(result)
        oqs = result['data']['node']
        self.assertEqual(oqs['config']['id'], config_id)
        self.assertEqual(oqs['modified_config']['id'], archive_id)

        return result

    def test_get_openquake_hazard_solution_node(self):
        result = self.test_create_openquake_hazard_solution()
        hazout_id = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

        query = '''
        query get_solution($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardSolution {
              created
            }
          }
        }
        '''
        result = self.client.execute(query, variable_values=dict(id=hazout_id))
        # print(result)

        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta)

    # def test_update_openquake_hazard_solution_node(self):
    #     result  = self.test_create_openquake_hazard_solution()
    #     hazout_id =  result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

    #     query = '''
    #     query get_solution($id: ID!) {
    #       node(id:$id) {
    #         __typename
    #         ... on OpenquakeHazardSolution {
    #           created
    #         }
    #       }
    #     }
    #     '''
    #     result = self.client.execute(query, variable_values=dict(id=hazout_id))
    #     print(result)

    #     delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
    #     max_delta = dt.timedelta(seconds=1)
    #     self.assertTrue(delta < max_delta )

    def test_create_openquake_hazard_solution_with_predecessors(self):
        upstream_sid = self.create_source_solution()  # File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid)  # File 100002
        nrml_id = inversion_solution_nrml['data']['create_inversion_solution_nrml']['inversion_solution_nrml']['id']

        archive = self.create_file("config_archive.zip")  # File 100003
        csv_archive = self.create_file("csv_archive.zip")  # File 100004
        csv_archive_id = csv_archive['data']['create_file']['file_result']['id']
        modconf_id = archive['data']['create_file']['file_result']['id']

        task_args_id = archive['data']['create_file']['file_result']['id']

        haztask = self.build_hazard_task()
        # print(haztask)
        haztask_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        predecessors = [dict(id=upstream_sid, depth=-2), dict(id=nrml_id, depth=-1)]

        query = '''
            mutation ($created: DateTime!, $csv_archive_id: ID!, $produced_by:ID!, $predecessors: [PredecessorInput],
                $modified_config_id: ID!, $task_args_id: ID!) {
              create_openquake_hazard_solution(
                  input: {
                      created: $created
                      csv_archive: $csv_archive_id
                      #hdf5_archive: $hdf5_archive_id
                      produced_by: $produced_by
                      predecessors: $predecessors
                      modified_config: $modified_config_id
                      task_args: $task_args_id
                  }

              )
              {
                ok
                openquake_hazard_solution { id
                    modified_config {id, file_name}
                    task_args {id, file_name}
                    csv_archive { id, file_name }
                    produced_by { id }
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
            }'''
        variables = dict(
            created=dt.datetime.now(tzutc()).isoformat(),
            csv_archive_id=csv_archive_id,
            produced_by=haztask_id,
            predecessors=predecessors,
            modified_config_id=modconf_id,
            task_args_id=task_args_id,
        )

        result = self.client.execute(query, variable_values=variables)
        # print(result)
        oqs = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']

        self.assertEqual(oqs['predecessors'][0]['depth'], -2)
        self.assertEqual(oqs['predecessors'][0]['relationship'], "Grandparent")
        return result

    def test_get_oq_hazard_solution_with_pred(self):
        result = self.test_create_openquake_hazard_solution_with_predecessors()
        hazout_id = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

        query = '''
        query get_openquake_hazard_solution($id: ID!) {
          node(id:$id) {
            __typename
            ... on OpenquakeHazardSolution {
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
        result = self.client.execute(query, variable_values=dict(id=hazout_id))
        # print(result)
        node = result['data']['node']
        self.assertEqual(node['predecessors'][0]['relationship'], 'Grandparent')
        self.assertEqual(node['predecessors'][1]['relationship'], 'Parent')
