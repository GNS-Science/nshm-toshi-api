"""
Test API function for GeneralTask
using moto mocking re issue #223
"""

import datetime as dt
import unittest

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import from_global_id
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

from .hazard.setup_helpers import SetupHelpersMixin


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

        upstream_sid = self.create_source_solution()
        self.new_gt = self.create_general_task()
        self.at_id = self.create_automation_task("SCALE_SOLUTION")
        self.create_gt_relation(self.new_gt, self.at_id)

        result = self.create_scaled_solution(upstream_sid, self.at_id)

        ss = result['data']['create_scaled_inversion_solution']['solution']
        self.scaled_solution_id = ss['id']

        # def create_task_file(self, task_id, file_id, role):
        qry2 = '''
        mutation create_file_relation(
            $thing_id:ID!
            $file_id:ID!
            $role:FileRole!) {
              create_file_relation(
                file_id:$file_id
                thing_id:$thing_id
                role:$role
              )
            {
              ok
            }
        }'''
        variables = dict(thing_id=self.at_id, file_id=self.at_id, role='WRITE')
        executed = self.client.execute(qry2, variable_values=variables)
        print('created file relation', executed)

    def test_general_task_query(self):
        print("self.new_gt", self.new_gt)

        qry = '''
            query GeneralTaskChildrenTabQuery($id: ID!) {
              node(id: $id) {
                ... on GeneralTask {
                  id
                  model_type
                  children {
                    edges {
                      node {
                        child {
                          __typename
                          ... on Node {
                            id
                          }
                          ...on AutomationTask {
                            task_type
                            inversion_solution {
                              __typename
                              ... on Node {
                                id
                              }
                            }
                          }
                          ... on AutomationTaskInterface {   
                            state
                            result
                            created
                            duration
                            arguments {
                              k
                              v
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }        

        '''

        print(qry)
        executed = self.client.execute(qry, variable_values=dict(id=self.new_gt))
        print(executed)

        node = executed['data']['node']
        assert node['id'] == self.new_gt
        assert node['children']['edges'][0]['node']['child']['__typename'] == "AutomationTask"
        assert node['children']['edges'][0]['node']['child']['inversion_solution']['__typename']
        assert node['children']['edges'][0]['node']['child']['inversion_solution']['id'] == self.scaled_solution_id
        assert (
            node['children']['edges'][0]['node']['child']['inversion_solution']['__typename']
            == "ScaledInversionSolution"
        )
