from graphql_api.schema.search_manager import SearchManager
from re import S
from graphql_api.data import data_manager
from unittest.case import skip
from graphql_api.config import REGION, S3_BUCKET_NAME
from io import BytesIO
from unittest import mock
import json

import datetime as dt
import unittest
from copy import copy
from dateutil.tz import tzutc
import boto3

from graphene.test import Client
from graphql_api import data
from moto import mock_dynamodb2, mock_s3
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject

import graphql_api.data
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.data.thing_data import ThingData

GT_DICT = {'attribute_values': {'object_content': {'id': 100000, 'created': '2022-03-03T00:17:52.352274+00:00', 'files': None, 'parents': None, 'children': [{'child_id': '100001', 'child_clazz': 'AutomationTask'}, {'child_id': '100002', 'child_clazz': 'AutomationTask'}], 'updated': None, 'agent_name': 'benc', 'title': 'TEST Build opensha rupture set Coulomb #1', 'description': None, 'argument_lists': None, 'swept_arguments': None, 'meta': None, 'notes': None, 'subtask_count': None, 'subtask_type': None, 'model_type': None, 'subtask_result': None, 'clazz_name': 'GeneralTask'}, 'object_id': 'ThingData/100000', 'object_type': 'ThingData', 'version': 3}}
AT_1_DICT = {'attribute_values': {'object_content': {'id': 100001, 'created': '2022-03-03T00:19:39.170876+00:00', 'files': None, 'parents': [{'parent_id': '100000', 'parent_clazz': 'GeneralTask'}], 'children': None, 'result': None, 'state': None, 'duration': None, 'arguments': None, 'environment': None, 'metrics': None, 'model_type': None, 'task_type': None, 'inversion_solution': None, 'clazz_name': 'AutomationTask'}, 'object_id': 'ThingData/100001', 'object_type': 'ThingData', 'version': 2}}
AT_2_DICT = {'attribute_values': {'object_content': {'id': 100002, 'created': '2022-03-03T00:20:05.690451+00:00', 'files': None, 'parents': [{'parent_id': '100000', 'parent_clazz': 'GeneralTask'}], 'children': None, 'result': None, 'state': None, 'duration': None, 'arguments': None, 'environment': None, 'metrics': None, 'model_type': None, 'task_type': None, 'inversion_solution': None, 'clazz_name': 'AutomationTask'}, 'object_id': 'ThingData/100002', 'object_type': 'ThingData', 'version': 2}}
GET_GT_CHILDREN = """query GeneralTaskChildrenTabQuery(
  $id: ID!
) {
  node(id: $id) {
    __typename
    ... on GeneralTask {
      id
      model_type
      children {
        edges {
          node {
            child {
              __typename
              ... on AutomationTask {
                __typename
                id
                created
                duration
                state
                result
                arguments {
                  k
                  v
                }
              }
              ... on RuptureGenerationTask {
                __typename
                id
                created
                duration
                state
                result
                arguments {
                  k
                  v
                }
              }
              ... on Node {
                __isNode: __typename
                id
              }
            }
            id
          }
        }
      }
    }
    id
  }
}"""

GET_INVERSION_CHILDREN_IDS = '''query InversionSolutionDiagnosticContainerQuery(
  $id: [ID!]
) {
  nodes(id_in: $id) {
    result {
      edges {
        node {
          __typename
          ... on AutomationTask {
            created
            task_type
            id
            inversion_solution {
              id
              file_name
              mfd_table_id
              meta {
                k
                v
              }
              tables {
                table_id
                table_type
              }
            }
          }
          ... on Node {
            __isNode: __typename
            id
          }
        }
      }
    }
  }
}'''
FIND_BY_ID_QUERY = '''
query FindQuery(
  $id: ID!
) {
  node(id: $id) {
    __typename
    id
  }
}'''
START_ID = 100000



@mock_dynamodb2
class TestGeneralTaskQueriesDB(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        ToshiThingObject.create_table()
        ToshiIdentity.create_table()
        self._s3 = boto3.resource('s3')
        self._client = boto3.client('s3')
        self._bucket_name = S3_BUCKET_NAME
        self._model = ToshiThingObject()
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake':'auth'}))
        self._connection = Connection(region=REGION)
        self._general_task = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._general_task.create(clazz_name='GeneralTask', created=dt.datetime.now(tzutc()), meta=None, 
                                  title='TEST Build opensha rupture set Coulomb #1', agent_name='benc')
        self._auto_task_1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._auto_task_2 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._auto_task_1.create(clazz_name='AutomationTask', created=dt.datetime.now(tzutc()))
        self._auto_task_2.create(clazz_name='AutomationTask', created=dt.datetime.now(tzutc()))
        self._general_task.add_child_relation(str(START_ID), str(START_ID+1), 'AutomationTask')
        self._general_task.add_child_relation(str(START_ID), str(START_ID+2), 'AutomationTask')
        self._auto_task_1.add_parent_relation(str(START_ID+1), str(START_ID), 'GeneralTask')
        self._auto_task_2.add_parent_relation(str(START_ID+2), str(START_ID), 'GeneralTask')
    
    def test_general_task_children_query(self):
         
        result = self.client.execute(GET_GT_CHILDREN, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})['data']['node']
        print(result)
        child_1 = result['children']['edges'][0]['node']['child']
        child_2 = result['children']['edges'][1]['node']['child']

        assert result['id'] == "R2VuZXJhbFRhc2s6MTAwMDAw"
        assert result['__typename'] == 'GeneralTask'
        assert child_1['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert child_2['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAy'

    
    def test_inversion_solution_diagnostics_query(self):
        result = self.client.execute(GET_INVERSION_CHILDREN_IDS, variable_values={'id': ['QXV0b21hdGlvblRhc2s6MTAwMDAx', 'QXV0b21hdGlvblRhc2s6MTAwMDAy']})
        data = result['data']['nodes']['result']['edges']
        print(data)
        assert data[0]['node']['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert data[1]['node']['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAy'
      
    def test_get_general_task_by_id_query(self):
        gt_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})
        assert gt_result['data']['node']['__typename'] == 'GeneralTask'
        at_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'QXV0b21hdGlvblRhc2s6MTAwMDAx'})
        print(at_result)
        assert at_result['data']['node']['__typename'] == 'AutomationTask'
        
        
    def tearDown(self) -> None:
        ToshiThingObject.delete_table()
        ToshiIdentity.delete_table()
        
# @mock_s3
# class TestGeneralTaskQueriesDB(unittest.TestCase):
#     mock_s3 = mock_s3()
#     bucket_name='nzshm22-toshi-api-test'
#     def setUp(self):
#         self.mock_s3.start()
#         self.client = Client(root_schema)
#         self._s3 = boto3.resource('s3')
#         self._client = boto3.client('s3')
#         self._client.create_bucket(Bucket=self.bucket_name)
#         self._bucket = self._s3.Bucket(self.bucket_name, client=self._client)
#         self._bucket.put_object(Key='ThingData/100000/object.json', Body=json.dumps(GT_DICT))
#         self._bucket.put_object(Key='ThingData/100001/object.json', Body=json.dumps(AT_1_DICT))
#         self._bucket.put_object(Key='ThingData/100002/object.json', Body=json.dumps(AT_2_DICT))
        
#     def tearDown(self):
#         self.mock_s3.stop()
        
#     def test_get_general_task_by_id_query(self):
#         result = self.client.execute(GET_INVERSION_CHILDREN_IDS, variable_values={'id': ['QXV0b21hdGlvblRhc2s6MTAwMDAx', 'QXV0b21hdGlvblRhc2s6MTAwMDAy']})
#         data = result['data']['nodes']['result']['edges']
#         print(data)
#         assert 0 