"""
Test API function for GeneralTask

Mocking our data layer

"""

import datetime as dt
import unittest
from unittest import mock

from dateutil.tz import tzutc
from graphene.test import Client

import graphql_api.data  # for mocking
from graphql_api.schema import root_schema

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


class IncrId:
    next_id = -1

    def get_next_id(self, *args):
        self.next_id += 1
        return self.next_id


TASKMOCK = lambda _self, _id: {
    "id": _id,
    "clazz_name": "GeneralTask",
    "created": "2020-10-30T09:15:00+00:00",
    "title": "max_jump_distance",
}


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', IncrId().get_next_id)
class TestGeneralTaskBug29(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)
        # migrate()

    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', TASKMOCK)
    @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
    @mock.patch(
        'graphql_api.data.thing_relation_data.ThingRelationData.create',
        lambda self, parent_clazz, child_clazz, parent_id, child_id: {},
    )
    def test_create_two_gts_and_link_them(self):
        # the first GT
        gt1_result = self.client.execute(CREATE_GT, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(gt1_result)
        assert gt1_result['data']['create_general_task']['general_task']['id'] == 'R2VuZXJhbFRhc2s6MA=='

        # the second
        gt2_result = self.client.execute(CREATE_GT, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(gt2_result)
        assert gt2_result['data']['create_general_task']['general_task']['id'] == 'R2VuZXJhbFRhc2s6MQ=='

        # finally the relation
        gt_link_result = self.client.execute(
            CREATE_GT_RELATION, variable_values=dict(parent_id='R2VuZXJhbFRhc2s6MA==', child_id='R2VuZXJhbFRhc2s6MQ==')
        )

        print('GTLINK ', gt_link_result)
        assert gt_link_result['data']['create_task_relation']['ok'] == True
