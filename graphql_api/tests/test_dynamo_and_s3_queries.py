import datetime as dt
import json
import unittest
from io import BytesIO

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.data.thing_data import ThingData
from graphql_api.dynamodb.models import ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

GT_DICT = {
    'id': 100000,
    'created': '2022-03-03T00:17:52.352274+00:00',
    'files': None,
    'parents': None,
    'children': [
        {'child_id': '100001', 'child_clazz': 'AutomationTask'},
        {'child_id': '100002', 'child_clazz': 'AutomationTask'},
    ],
    'updated': None,
    'agent_name': 'benc',
    'title': 'TEST Build opensha rupture set Coulomb #1',
    'description': None,
    'argument_lists': None,
    'swept_arguments': None,
    'meta': None,
    'notes': None,
    'subtask_count': None,
    'subtask_type': None,
    'model_type': None,
    'subtask_result': None,
    'clazz_name': 'GeneralTask',
}
AT_1_DICT = {
    'id': 100001,
    'created': '2022-03-03T00:19:39.170876+00:00',
    'files': None,
    'parents': [{'parent_id': '100000', 'parent_clazz': 'GeneralTask'}],
    'children': None,
    'result': None,
    'state': None,
    'duration': None,
    'arguments': None,
    'environment': None,
    'metrics': None,
    'model_type': None,
    'task_type': None,
    'inversion_solution': None,
    'clazz_name': 'AutomationTask',
}
AT_2_DICT = {
    'id': '100002',
    'created': '2022-03-03T00:20:05.690451+00:00',
    'files': None,
    'parents': [{'parent_id': '100000', 'parent_clazz': 'GeneralTask'}],
    'children': None,
    'result': None,
    'state': None,
    'duration': None,
    'arguments': None,
    'environment': None,
    'metrics': None,
    'model_type': None,
    'task_type': None,
    'inversion_solution': None,
    'clazz_name': 'AutomationTask',
}
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
            # id
          }
        }
      }
    }
    id
  }
}"""

GET_GT = '''query GeneralTaskQuery(
  $id: ID!
) {
  node(id: $id) {
    __typename
    ... on GeneralTask {
      id
      title
      description
      notes
      created
      updated
      agent_name
      model_type
      subtask_type
      subtask_count
      subtask_result
      argument_lists {
        k
        v
      }
      swept_arguments
      children {
        total_count
      }
    }
    id
  }
}'''

GET_AT = '''
query AutomationTaskQuery(
  $id: ID!
) {
  node(id: $id) {
    __typename
    id
    ... on AutomationTask {
      id
      duration
      created
      result
      state
      task_type
      model_type
      files {
        edges {
          node {
            role
            file {
              __typename
              ... on Node {
                __isNode: __typename
                id
              }
              ... on FileInterface {
                __isFileInterface: __typename
                file_name
                file_url
              }
            }
          }
        }
      }
      arguments {
        k
        v
      }
      environment {
        k
        v
      }
      metrics {
        k
        v
      }
      parents {
        edges {
          node {
            parent {
              id
            }
          }
        }
      }
    }
  }
}
'''

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


@mock_dynamodb
class TestGeneralTaskQueriesDB(unittest.TestCase):
    def setUp(self):
        self.client = Client(root_schema)
        ToshiThingObject.create_table()
        ToshiIdentity.create_table()
        self._s3 = boto3.resource('s3')
        self._client = boto3.client('s3')
        self._bucket_name = S3_BUCKET_NAME
        self._model = ToshiThingObject()
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))
        self._connection = Connection(region=REGION)
        self._general_task = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._general_task.create(
            clazz_name='GeneralTask',
            created=dt.datetime.now(tzutc()),
            meta=None,
            title='TEST Build opensha rupture set Coulomb #1',
            agent_name='benc',
        )
        self._auto_task_1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._auto_task_2 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._auto_task_1.create(clazz_name='AutomationTask', created=dt.datetime.now(tzutc()))
        self._auto_task_2.create(clazz_name='AutomationTask', created=dt.datetime.now(tzutc()))
        self._inversion = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._inversion.create(clazz_name='InversionSolution', created=dt.datetime.now(tzutc()))

        self._data_manager.thing_relation.create(
            parent_clazz='GeneralTask',
            child_clazz='AutomationTask',
            parent_id=str(START_ID),
            child_id=str(START_ID + 1),
        )

        self._data_manager.thing_relation.create(
            parent_clazz='GeneralTask',
            child_clazz='AutomationTask',
            parent_id=str(START_ID),
            child_id=str(START_ID + 2),
        )

    def test_get_gt(self):
        result = self.client.execute(GET_GT, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})['data']['node']
        print(result)
        assert result['id'] == "R2VuZXJhbFRhc2s6MTAwMDAw"
        assert result['__typename'] == 'GeneralTask'
        assert result['children']['total_count'] == 2

    def test_general_task_children_query(self):
        data = self.client.execute(GET_GT_CHILDREN, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})
        result = data['data']['node']
        child_1 = result['children']['edges'][0]['node']['child']
        child_2 = result['children']['edges'][1]['node']['child']
        print(result)
        assert result['id'] == "R2VuZXJhbFRhc2s6MTAwMDAw"
        assert result['__typename'] == 'GeneralTask'
        assert child_1['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert child_2['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAy'

    def test_get_by_id_query(self):
        gt_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})
        assert gt_result['data']['node']['__typename'] == 'GeneralTask'
        print(f'GT: {gt_result}')
        at_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'QXV0b21hdGlvblRhc2s6MTAwMDAx'})
        print(f'AT: {at_result}')
        assert at_result['data']['node']['__typename'] == 'AutomationTask'

    def test_get_automation_task(self):
        result = self.client.execute(GET_AT, variable_values={'id': 'QXV0b21hdGlvblRhc2s6MTAwMDAx'})
        print(f"Result: {result}")
        data = result['data']['node']
        assert data['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert data['parents']['edges'][0]['node']['parent']['id'] == 'R2VuZXJhbFRhc2s6MTAwMDAw'
        assert data['__typename'] == 'AutomationTask'

    def tearDown(self) -> None:
        ToshiThingObject.delete_table()
        ToshiIdentity.delete_table()


@mock_s3
@mock_dynamodb
class TestGeneralTaskQueriesS3(unittest.TestCase):
    def setUp(self):
        self.client = Client(root_schema)
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3.Bucket(S3_BUCKET_NAME)
        self._connection = Connection(region=REGION)
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))
        self._gt = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._at_1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._at_2 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        self._bucket.put_object(Key='ThingData/100000/object.json', Body=json.dumps(GT_DICT))
        self._bucket.put_object(Key='ThingData/100001/object.json', Body=json.dumps(AT_1_DICT))
        self._bucket.put_object(Key='ThingData/100002/object.json', Body=json.dumps(AT_2_DICT))

    def test_s3_create(self):
        # bucket S3_BUCKET_NAME_unconfigured, key=FileData/1587.0nVoFt/object.json, client=
        print(f"S3_BUCKET_NAME {S3_BUCKET_NAME}")
        assert S3_BUCKET_NAME == "S3_BUCKET_NAME_unconfigured"
        s3obj = self._s3.Object(S3_BUCKET_NAME, 'ThingData/100002/object.json')
        file_object = BytesIO()
        s3obj.download_fileobj(file_object)
        file_object.seek(0)

        obj = json.load(file_object)
        assert obj['id'] == '100002'

    def test_general_task_children_query(self):
        result = self.client.execute(GET_GT_CHILDREN, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})['data'][
            'node'
        ]
        print(result)
        child_1 = result['children']['edges'][0]['node']['child']
        child_2 = result['children']['edges'][1]['node']['child']

        assert result['id'] == "R2VuZXJhbFRhc2s6MTAwMDAw"
        assert result['__typename'] == 'GeneralTask'
        assert child_1['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert child_2['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAy'

    def test_get_by_id_query(self):
        gt_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})
        print(gt_result)
        assert gt_result['data']['node']['__typename'] == 'GeneralTask'
        at_result = self.client.execute(FIND_BY_ID_QUERY, variable_values={'id': 'QXV0b21hdGlvblRhc2s6MTAwMDAx'})
        print(at_result)
        assert at_result['data']['node']['__typename'] == 'AutomationTask'

    def test_get_gt(self):
        result = self.client.execute(GET_GT, variable_values={'id': 'R2VuZXJhbFRhc2s6MTAwMDAw'})['data']['node']
        print(result)
        assert result['id'] == "R2VuZXJhbFRhc2s6MTAwMDAw"
        assert result['__typename'] == 'GeneralTask'
        assert result['children']['total_count'] == 2

    def test_get_automation_task(self):
        result = self.client.execute(GET_AT, variable_values={'id': 'QXV0b21hdGlvblRhc2s6MTAwMDAx'})['data']['node']
        print(result)
        assert result['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert result['parents']['edges'][0]['node']['parent']['id'] == 'R2VuZXJhbFRhc2s6MTAwMDAw'
        assert result['__typename'] == 'AutomationTask'
