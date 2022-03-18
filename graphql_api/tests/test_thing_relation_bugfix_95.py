
"""
Test API function for GeneralTask

Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data

from graphql_api.schema import root_schema
from graphql_api.schema.custom import StrongMotionStation
from graphql_api.dynamodb.models import migrate
from moto import mock_dynamodb2

import graphql_api.data # for mocking

CREATE_GT = '''
    mutation new_gt ($created: DateTime!) {
      create_general_task(input:{
        created: $created
        title: "TEST Build opensha rupture set Coulomb #1"
        description:"Using "
        agent_name:"chrisbc"
      })
      {
        general_task{
          id
        }
      }
    }
'''

CREATE_RUPTGEN_TASK = '''
    mutation ($created: DateTime!) {
        create_rupture_generation_task(input: {
            state: UNDEFINED
            result: UNDEFINED
            created: $created
            duration: 600

            arguments: [
                { k:"max_jump_distance" v: "55.5" }
                { k:"max_sub_section_length" v: "2" }
                { k:"max_cumulative_azimuth" v: "590" }
                { k:"min_sub_sections_per_parent" v: "2" }
                { k:"permutation_strategy" v: "DOWNDIP" }
            ]

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"gitref_opensha_commons" v: "ABC"}
                { k:"gitref_opensha_core" v: "ABC"}
                { k:"nshm_nz_opensha" v: "ABC"}
                { k:"host" v:"tryharder-ubuntu"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

            ##EXTRA_INPUT##

            }
            )
            {
                task_result {
                id
                created
                duration
                arguments {k v}
            }
        }
    }
'''

CREATE_GT_RELATION = '''
    mutation new_gt_link ($parent_id: ID!, $child_id: ID!) {
      create_task_relation(
        parent_id: $parent_id
        child_id: $child_id
      )
      {
        ok
        thing_relation { child_id }
      }
    }
'''

QUERY_RUPTGEN_PARENT = '''
query get_task {
      node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
          __typename
        ... on RuptureGenerationTask {
          id
          created
          duration
          state
          result
          parents {
            edges {
              node {
                parent {
                  ... on GeneralTask {
                    id
                    title
                    description
                  }
                }
              }
            }
          }
        }
      }
    }
'''



class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return self.next_id

TASKMOCK = lambda _self, _id: {
    "id": _id,
    "clazz_name": "GeneralTask",
    "created": "2020-10-30T09:15:00+00:00",
    "title": "max_jump_distance"
    }

RUPTMOCK = {'id': 0, "clazz_name": "RuptureGenerationTask",  'created': '2022-10-10T23:00:00+00:00', 'files': None, 'parents': [{'parent_id': '1', 'parent_clazz': 'GeneralTask'}], 'children': None, 'result': 'undefined', 'state': 'undefined', 'duration': 600.0, 'arguments': [{'k': 'max_jump_distance', 'v': '55.5'}, {'k': 'max_sub_section_length', 'v': '2'}, {'k': 'max_cumulative_azimuth', 'v': '590'}, {'k': 'min_sub_sections_per_parent', 'v': '2'}, {'k': 'permutation_strategy', 'v': 'DOWNDIP'}], 'environment': [{'k': 'gitref_opensha_ucerf3', 'v': 'ABC'}, {'k': 'gitref_opensha_commons', 'v': 'ABC'}, {'k': 'gitref_opensha_core', 'v': 'ABC'}, {'k': 'nshm_nz_opensha', 'v': 'ABC'}, {'k': 'host', 'v': 'tryharder-ubuntu'}, {'k': 'JAVA', 'v': '-Xmx24G'}], 'metrics': None,}
GENMOCK = {'id': 1, "clazz_name": "GeneralTask", 'created': '2022-10-10T23:00:00+00:00', 'files': None, 'parents': None, 'children': [{'child_id': '0', 'child_clazz': 'RuptureGenerationTask'}], 'updated': None, 'agent_name': 'benc', 'title': 'My Third Manual task', 'description': '##Some notes go here', 'argument_lists': None, 'swept_arguments': None, 'meta': None, 'notes': None, 'subtask_count': None, 'subtask_type': None, 'model_type': None, 'subtask_result': None}

@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', IncrId().get_next_id)
class TestGeneralTaskBug29(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)
        # migrate()

    @mock.patch('graphql_api.data.BaseData._read_object', TASKMOCK)
    @mock.patch('graphql_api.data.thing_relation_data.ThingRelationData.create', lambda self, parent_clazz, child_clazz, parent_id, child_id: {})
    @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
    def test_create_gt_and_ruptgen_and_link_them(self):
        # the first GT
        gt_result = self.client.execute(CREATE_GT, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(gt_result)
        assert gt_result['data']['create_general_task']\
                        ['general_task']['id'] == 'R2VuZXJhbFRhc2s6MA=='

        # the second
        ruptgen_result = self.client.execute(CREATE_RUPTGEN_TASK, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(ruptgen_result)
        assert ruptgen_result['data']['create_rupture_generation_task']\
                        ['task_result']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE='


        # finally the relation
        gt_link_result = self.client.execute(CREATE_GT_RELATION, variable_values=dict(
            parent_id='R2VuZXJhbFRhc2s6MA==',
            child_id='UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE='))

        print('GTLINK ', gt_link_result)
        assert gt_link_result['data']['create_task_relation']\
                        ['ok'] == True
                        
        with mock.patch('graphql_api.data.BaseData._read_object', side_effect=[RUPTMOCK, GENMOCK, GENMOCK]):  
            ruptgen_parent_query = self.client.execute(QUERY_RUPTGEN_PARENT, variable_values=dict(created=dt.datetime.now(tzutc())))
            print('RUPTGEN_PARENT', ruptgen_parent_query)
            result = ruptgen_parent_query['data']['node']
            assert result['parents']['edges'][0]['node']['parent']\
                        ['id'] == "R2VuZXJhbFRhc2s6MQ=="
            assert result['parents']['edges'][0]['node']['parent']\
                        ['title'] == "My Third Manual task"
            assert result['parents']['edges'][0]['node']['parent']\
                        ['description'] == "##Some notes go here"
            assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
