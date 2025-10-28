import datetime as dt
import unittest

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import from_global_id
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking
from setup_helpers import SetupHelpersMixin

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.custom.common import AggregationFn, TaskSubType
from graphql_api.schema.search_manager import SearchManager


@mock_dynamodb
@mock_s3
class TestAggregateInversionSolution(unittest.TestCase, SetupHelpersMixin):
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

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()
        self.common_ruptset_id = self.create_file("myruptset.zip", self.source_solution)['data']['create_file'][
            'file_result'
        ]['id']

    def test_create_an_aggregate_solution_task(self):
        self.create_automation_task("AGGREGATE_SOLUTION")

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['task_type'], TaskSubType.AGGREGATE_SOLUTION.value
        )

    def test_create_aggregate_solution(self):
        at_id = self.create_automation_task("AGGREGATE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_aggregate_solution([upstream_sid], at_id, AggregationFn.MEAN.name, self.common_ruptset_id)

        ss = result['data']['create_aggregate_inversion_solution']['solution']

        self.assertIn(upstream_sid, [sid['id'] for sid in ss['source_solutions']])

        print(ToshiFileObject.get("100003").object_content)
        self.assertEqual(ToshiFileObject.get("100003").object_content['id'], int(from_global_id(ss['id'])[1]))

    def test_create_aggregate_solution_with_common_rupture_id(self):
        at_id = self.create_automation_task("AGGREGATE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_aggregate_solution([upstream_sid], at_id, AggregationFn.MEAN.name, self.common_ruptset_id)

        asol = result['data']['create_aggregate_inversion_solution']['solution']

        self.assertEqual(asol['common_rupture_set']['id'], self.common_ruptset_id)

    # def test_create_aggregate_solution_with_predecessors(self):
    #     at_id = self.create_automation_task("AGGREGATE_SOLUTION")
    #     upstream_sid = self.create_source_solution()
    #     result = self.create_aggregate_solution_with_predecessors([upstream_sid, at_id, AggregationFn.MEAN.name)
    #     ss =  result['data']['create_scaled_inversion_solution']['solution']

    #     self.assertEqual(ss['source_solution']['id'], upstream_sid)
    #     print(ToshiFileObject.get("100002").object_content)

    def test_get_aggregate_solution_node(self):
        at_id = self.create_automation_task("AGGREGATE_SOLUTION")

        print(f"AT_ID {at_id}")
        upstream_sid = self.create_source_solution()
        result = self.create_aggregate_solution([upstream_sid], at_id, 'MEAN', self.common_ruptset_id)

        ss_id = result['data']['create_aggregate_inversion_solution']['solution']['id']

        query = '''
            query get_aggregate_solution($id: ID!) {
              node(id:$id) {
                __typename
                ... on AggregateInversionSolution {
                    created
                    produced_by { ... on Node{id} }
                    aggregation_fn
                    common_rupture_set { id }
                    source_solutions { ... on Node{id} }

                }
              }
            }
        '''
        result = self.client.execute(query, variable_values=dict(id=ss_id))
        print(result)
        node = result['data']['node']
        delta = dt.datetime.now(tzutc()) - dt.datetime.fromisoformat(node['created'])
        max_delta = dt.timedelta(seconds=1)
        self.assertTrue(delta < max_delta)
        self.assertIn(upstream_sid, [sid['id'] for sid in node['source_solutions']])
        self.assertEqual(node['produced_by']['id'], at_id)
        self.assertEqual(node['aggregation_fn'], 'MEAN')

    def test_get_aggregate_solution_with_predecessors(self):
        at_id = self.create_automation_task("AGGREGATE_SOLUTION")
        upstream_sid = self.create_source_solution()
        result = self.create_aggregate_solution_with_predecessors([upstream_sid], at_id, self.common_ruptset_id)
        result['data']['create_aggregate_inversion_solution']['solution']
        ss_id = result['data']['create_aggregate_inversion_solution']['solution']['id']
        query = '''
            query get_aggregate_solution($id: ID!) {
              node(id:$id) {
                __typename
                ... on AggregateInversionSolution {
                    created
                    produced_by { ... on Node {id} }
                    source_solutions { ... on Node {id} }
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
        result = self.client.execute(query, variable_values=dict(id=ss_id))
        print(result)
        node = result['data']['node']

        self.assertEqual(node['produced_by']['id'], at_id)
        self.assertEqual(node['predecessors'][0]['id'], upstream_sid)
        self.assertEqual(node['predecessors'][0]['relationship'], 'Parent')
