"""
Test API function for GeneralTask
using moto mocking
"""

import datetime as dt
import unittest
from unittest import mock

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
    @mock.patch('graphql_api.schema.search_manager.Elasticsearch')
    def setUp(self, mock_es_class):
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

        upstream_sid = self.create_source_solution()
        self.new_gt = self.create_general_task()
        self.at_id = self.create_automation_task("SCALE_SOLUTION")
        self.create_gt_relation(self.new_gt, self.at_id)

        result = self.create_scaled_solution(upstream_sid, self.at_id)

        ss = result['data']['create_scaled_inversion_solution']['solution']
        # self.assertEqual(ss['source_solution']['id'], upstream_sid)

        # print(ToshiFileObject.get("100001").object_content)

        # # object ID is stored internally as an INT
        # self.assertEqual(ToshiFileObject.get("100001").object_content['id'], int(from_global_id(ss['id'])[1]))

        self.scaled_solution_id = ss['id']

    def test_nodes_query(self):
        print("self.scaled_solution_id", self.scaled_solution_id)
        qry = (
            '''
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
        }'''
            % self.scaled_solution_id
        )

        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        node = executed['data']['nodes']['result']['edges'][0]['node']
        assert node['id'] == self.scaled_solution_id
        assert node['__typename'] == "ScaledInversionSolution"

    def test_nodes_query_expand_solution(self):
        print("self.scaled_solution_id", self.scaled_solution_id)
        qry = (
            '''
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
                  ... on InversionSolutionInterface {
                    produced_by { ... on Node{id} }
                  }
                  # ... on PredecessorsInterface {
                  #   predecessors {
                  #       typename
                  #       relationship
                  #       node {
                  #           __typename
                  #           ... on Node{ id }
                  #       }
                  #       depth
                  #   }
                  # }
                  ...  on FileInterface {
                    file_name
                    file_size
                  }
                  ... on ScaledInversionSolution {
                    source_solution { ... on Node{id} }
                  }
                }
              }
            }
          }
        }'''
            % self.scaled_solution_id
        )

        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        node = executed['data']['nodes']['result']['edges'][0]['node']
        assert node['id'] == self.scaled_solution_id
        assert node['__typename'] == "ScaledInversionSolution"
        assert node['source_solution']
        assert node['source_solution']['id']
        assert node['produced_by']
        assert node['produced_by']['id']

    def test_nodes_query_expand_solution_task_hierarchy(self):
        print("self.scaled_solution_id", self.scaled_solution_id)
        qry = (
            '''
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
                  ... on InversionSolutionInterface {
                    produced_by {
                        __typename
                        ... on Node{id} # the AutomationTask
                        ... on AutomationTaskInterface {
                            parents {
                                edges {
                                    node {
                                        parent {
                                            ... on Node { id } # the GT id
                                            ... on GeneralTask {
                                                meta {k v}
                                                title
                                                description
                                                created
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                  }
                }
              }
            }
          }
        }'''
            % self.scaled_solution_id
        )

        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        node = executed['data']['nodes']['result']['edges'][0]['node']
        assert node['id'] == self.scaled_solution_id
        assert node['__typename'] == "ScaledInversionSolution"
        assert node['produced_by']
        assert node['produced_by']['id']
        assert node['produced_by']['parents']['edges'][0]['node']['parent']['title']
