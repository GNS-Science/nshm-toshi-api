"""
Test API function for GeneralTask
using moto mocking
"""
import datetime as dt
import unittest

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking
from .hazard.setup_helpers import SetupHelpersMixin

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

from graphql_relay import from_global_id

@mock_dynamodb
@mock_s3
class TestScaledInversionSolution(unittest.TestCase, SetupHelpersMixin):
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

        at_id = self.create_automation_task("SCALE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_scaled_solution(upstream_sid, at_id)

        ss = result['data']['create_scaled_inversion_solution']['solution']
        # self.assertEqual(ss['source_solution']['id'], upstream_sid)

        # print(ToshiFileObject.get("100001").object_content)

        # # object ID is stored internally as an INT
        # self.assertEqual(ToshiFileObject.get("100001").object_content['id'], int(from_global_id(ss['id'])[1]))

        self.scaled_solution_id = ss['id']



    def test_nodes_query(self):
        print("self.scaled_solution_id", self.scaled_solution_id)


        qry = '''
        query q0 {
          nodes(id_in: ["%s"]) {
            ok
            result {
              edges {
                node {
                  __typename
                  ... on Node {
                    id
                  }
                }
              }
            }
          }
        }''' % self.scaled_solution_id

        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        node = executed['data']['nodes']['result']['edges'][0]['node']
        assert node['id'] == self.scaled_solution_id
        assert node['__typename'] == "ScaledInversionSolution"
        # assert node['inversion_solution']['id'] == "SW52ZXJzaW9uU29sdXRpb246MC4wbXFjN2Y="
        # assert node['inversion_solution']['file_name'] == "solution.zip"


