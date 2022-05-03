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

    def test_create_openquake_hazard_solution(self):
        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id =  inversion_solution_nrml['data']['create_inversion_solution_nrml']\
            ['inversion_solution_nrml']['id']

        archive = self.create_file("config_archive.zip") #File 100003
        archive_id = archive['data']['create_file']['file_result']['id']
        result = self.create_openquake_config([nrml_id], archive_id) #Thing 100000
        config_id = result['data']['create_openquake_hazard_config']['config']['id']


        csv_archive = self.create_file("csv_archive.zip") #File 100004
        csv_archive_id = csv_archive['data']['create_file']['file_result']['id']
        # self.assertEqual(
        #     ToshiThingObject.get("100000").object_content['clazz_name'], 'OpenquakeHazardConfig' )

        haztask = self.build_hazard_task()
        print(haztask)
        haztask_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        query = '''
            mutation ($created: DateTime!, $config_id: ID!, $csv_archive_id: ID!, $produced_by:ID!) {
              create_openquake_hazard_solution(
                  input: {
                      created: $created
                      config: $config_id
                      csv_archive: $csv_archive_id
                      #hdf5_archive: $hdf5_archive_id
                      produced_by: $produced_by
                  }
              )
              {
                ok
                openquake_hazard_solution { id
                    config { template_archive { id, file_name }}
                    csv_archive { id, file_name }
                    produced_by { id }
                }
              }
            }'''
        variables = dict(created=dt.datetime.now(tzutc()).isoformat(), config_id = config_id,
            csv_archive_id=csv_archive_id, produced_by=haztask_id )

        result = self.client.execute(query, variable_values=variables )
        print(result)
        oqs = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']
        self.assertEqual(oqs['config']['template_archive']['file_name'], "config_archive.zip")
        self.assertEqual(oqs['csv_archive']['file_name'], "csv_archive.zip")
        self.assertEqual(oqs['produced_by']['id'], haztask_id)
        return result


    def test_get_openquake_hazard_solution_node(self):
        result  = self.test_create_openquake_hazard_solution()
        hazout_id =  result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']['id']

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
        print(result)

        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(result['data']['node']['created'])
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta )

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
        upstream_sid = self.create_source_solution() #File 100001
        inversion_solution_nrml = self.create_inversion_solution_nrml(upstream_sid) #File 100002
        nrml_id = inversion_solution_nrml['data']['create_inversion_solution_nrml']\
            ['inversion_solution_nrml']['id']

        archive = self.create_file("config_archive.zip") #File 100003
        archive_id = archive['data']['create_file']['file_result']['id']
        result = self.create_openquake_config([nrml_id], archive_id) #Thing 100000
        config_id = result['data']['create_openquake_hazard_config']['config']['id']
        csv_archive = self.create_file("csv_archive.zip") #File 100004
        csv_archive_id = csv_archive['data']['create_file']['file_result']['id']

        haztask = self.build_hazard_task()
        print(haztask)
        haztask_id = haztask['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']

        predecessors = [
            dict(id=upstream_sid, depth=-2),
            dict(id=nrml_id, depth=-1)
        ]

        query = '''
            mutation ($created: DateTime!, $config_id: ID!, $csv_archive_id: ID!, $produced_by:ID!, $predecessors: [PredecessorInput]) {
              create_openquake_hazard_solution(
                  input: {
                      created: $created
                      config: $config_id
                      csv_archive: $csv_archive_id
                      #hdf5_archive: $hdf5_archive_id
                      produced_by: $produced_by
                      predecessors: $predecessors
                  }

              )
              {
                ok
                openquake_hazard_solution { id
                    config { template_archive { id, file_name }}
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
        variables = dict(created=dt.datetime.now(tzutc()).isoformat(), config_id = config_id,
            csv_archive_id=csv_archive_id, produced_by=haztask_id, predecessors=predecessors )

        result = self.client.execute(query, variable_values=variables )
        print(result)
        oqs = result['data']['create_openquake_hazard_solution']['openquake_hazard_solution']

        self.assertEqual(oqs['predecessors'][0]['depth'], -2)
        self.assertEqual(oqs['predecessors'][0]['relationship'], "Grandparent")