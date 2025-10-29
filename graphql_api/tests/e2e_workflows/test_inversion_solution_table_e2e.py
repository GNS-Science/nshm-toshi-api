import unittest

import boto3
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiTableObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager


@mock_dynamodb
@mock_s3
class TestInversionSolutionWithMFDWorkflow(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)

        # S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)

        # Dynamo
        self._connection = Connection(region=REGION)

        ToshiTableObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))

    def test_link_inversion_solution_with_mfd_table(self):

        SETUP = '''
        mutation m0 {
          create_inversion_solution(input: {file_name: "MyINversion", file_size: 200}) {
            ok
            inversion_solution {
              id
            }
          }

          create_table(
            input: {
                object_id: "R2VuZXJhbFRhc2s6MjE3Qk1YREw=",
                created: "2021-06-11T02:37:26.009506+00:00",
                rows: [["1", "1.01"], ["2", "2.2"]], meta: [{k: "some_metric", v: "20"}],
                table_type: MFD_CURVES_V2,
                dimensions: [
                    {k: "grid_spacings", v: ["0.1"]},
                    {k: "IML_periods", v: ["0", "0.1"]}, {k: "tags", v: ["opensha", "testing"]}, {k: "gmpes", v: ["ASK_2014"]}]}
          ) {

            table {
              id
              table_type
            }
          }

          append_inversion_solution_tables(
            input: {id: "SW52ZXJzaW9uU29sdXRpb246MTAwMDAw", tables: [{produced_by_id: "PRODUCER_ID",
            label: "MyLabelledTable", table_id: "VGFibGU6MTAwMDAw", table_type: MFD_CURVES_V2}]}
          ) {
            ok
          }
        }'''

        result = self.client.execute(SETUP)
        print(result)
        # assert 0
        VERIFY = '''
        query {
          node(id: "SW52ZXJzaW9uU29sdXRpb246MTAwMDAw") {
            __typename
            ... on InversionSolution {
              id
              created
              file_name
              # mfd_table_id
              mfd_table { id }
              # hazard_table_id
              created
            }
          }
        }
        '''
        result = self.client.execute(VERIFY)

        print(result)
        assert not result.get('errors')
        assert result['data']['node']['mfd_table']['id']
        assert result['data']['node']['mfd_table']['id'] == 'VGFibGU6MTAwMDAw'
