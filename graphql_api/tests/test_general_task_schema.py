
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
from graphql_api import data_s3

from graphql_api.schema import root_schema

import graphql_api.data_s3 # for mocking


class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return self.next_id

READ_MOCK = lambda _self, id: dict(
    id = "0",
    clazz_name = "GeneralTask",
    agent_name = "DonDuck",
    created = "2021-06-11T02:37:26.009506+00:00",
    argument_lists = [{"k": "bogus_metric", "v": ["20", "25"]}, {"k": "unswept_metric", "v": [None]}],
    meta = [{ "k":"some_metric", "v": "55.5" }],
    notes="dum de dum",
    subtask_count=4,
    subtask_type="rupture_set",
    model_type="subduction",
    subtask_result="partial"
    )

@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', IncrId().get_next_id)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body:  {})
class TestBasicGeneralTaskOperations(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)

    # @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_create_general_task(self):
        CREATE_QRY = '''
            mutation { #($file_name: String!, $file_size: Int!, $produced_by: ID!, $mfd_table: ID!)
              create_general_task(input: {
                  agent_name:"XO"
                  title:"The title"
                  description:"a description"
                  created: "2021-08-03T01:38:21.933731+00:00"
                  argument_lists: {k: "some_metric", v: ["20", "25"]}
              })
              {
                  general_task {
                    id
                    created
                  }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID", mfd_table="TABLE_ID"))
        print(result)
        assert result['data']['create_general_task']['general_task']['id'] == 'R2VuZXJhbFRhc2s6MA=='


    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_general_task_by_node_id(self):
        # the first GT
        qry = '''
        query get_GT {
          node(id:"R2VuZXJhbFRhc2s6MA==") {
            __typename
            ... on GeneralTask {
              created
              id
              agent_name
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'R2VuZXJhbFRhc2s6MA=='
        assert result['data']['node']['agent_name'] == "DonDuck"

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_general_task_swept_args(self):
        # the first GT
        qry = '''
        query get_GT {
          node(id:"R2VuZXJhbFRhc2s6MA==") {
            __typename
            ... on GeneralTask {
              id
              argument_lists {k v}
              swept_arguments
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'R2VuZXJhbFRhc2s6MA=='

        assert result['data']['node']['argument_lists'][0]['k'] == "bogus_metric"
        assert result['data']['node']['argument_lists'][0]['v'] == ["20", "25"]
        assert result['data']['node']['swept_arguments'] == ["bogus_metric"]
        assert result['data']['node']['argument_lists'][1]['k'] == "unswept_metric"
        assert result['data']['node']['argument_lists'][1]['v'] == [None]


@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', IncrId().get_next_id)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body:  {})
class TestExtraGeneralTaskOperations(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_general_task_notes_and_meta(self):
        # the first GT
        qry = '''
        query get_GT {
          node(id:"R2VuZXJhbFRhc2s6MA==") {
            __typename
            ... on GeneralTask {
              id
              notes
              meta{k v}
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'R2VuZXJhbFRhc2s6MA=='

        assert result['data']['node']['notes'] == "dum de dum"
        assert result['data']['node']['meta'][0]['k'] == "some_metric"
        assert result['data']['node']['meta'][0]['v'] == "55.5"

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_general_task_others(self):
        # the first GT
        qry = '''
        query get_GT {
          node(id:"R2VuZXJhbFRhc2s6MA==") {
            __typename
            ... on GeneralTask {
              id
              subtask_count
              subtask_type
              model_type
              subtask_result
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'R2VuZXJhbFRhc2s6MA=='
        assert result['data']['node']['subtask_count'] == 4
        assert result['data']['node']['subtask_type'] == "RUPTURE_SET"
        assert result['data']['node']['model_type'] == "SUBDUCTION"
        assert result['data']['node']['subtask_result'] == "PARTIAL"


    def test_create_general_task(self):
        CREATE_QRY = '''
            mutation { #($file_name: String!, $file_size: Int!, $produced_by: ID!, $mfd_table: ID!)
              create_general_task(input: {
                  agent_name:"XO"
                  title:"The title"
                  description:"a description"
                  created: "2021-08-03T01:38:21.933731+00:00"
                  argument_lists: [{k: "some_metric", v: ["20", "25"]}]
                  meta: [{k: "some_metric", v: "20"}]
                  subtask_count: 16
                  model_type: CRUSTAL
                  subtask_result: SUCCESS
              })
              {
                  general_task {
                    id
                    meta {k v}
                    subtask_count
                    model_type
                    subtask_result
                  }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID", mfd_table="TABLE_ID"))
        print(result)
        assert result['data']['create_general_task']['general_task']['id'] == 'R2VuZXJhbFRhc2s6MA=='
        assert result['data']['create_general_task']['general_task']['meta'][0]['k'] == "some_metric"
        assert result['data']['create_general_task']['general_task']['meta'][0]['v'] == "20"
        assert result['data']['create_general_task']['general_task']['subtask_count'] == 16
        assert result['data']['create_general_task']['general_task']['model_type'] == "CRUSTAL"
        assert result['data']['create_general_task']['general_task']['subtask_result'] == "SUCCESS"


@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestUpdateGeneralTask(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_update_with_typical_fields(self):
        qry = '''
            mutation {
                update_general_task(input: {
                    task_id: "R2VuZXJhbFRhc2s6MA=="
                    #duration: 909,
                    meta: [{k: "balderdash" v: "20"}]
                    updated: "2021-08-03T01:38:21.933731+00:00"
                })
                {
                    general_task {
                        id
                        created
                        updated
                        #duration
                        meta {k v}
                        subtask_count
                        swept_arguments
                        argument_lists {k v}
                    }
                }
            }
        '''
        executed = self.client.execute(qry)
        print(executed)
        result = executed['data']['update_general_task']['general_task']
        assert result['id'] == 'R2VuZXJhbFRhc2s6MA=='
        #assert result['duration'] == 909
        assert result['updated'] == "2021-08-03T01:38:21.933731+00:00"
        assert result['meta'][0]['k'] == "balderdash"
        assert result['meta'][0]['v'] == "20"
        assert result['subtask_count'] == 4
        assert result['argument_lists'] == [{"k": "bogus_metric", "v": ["20", "25"]}, {"k": "unswept_metric", "v": [None]}]
        assert result['swept_arguments'] == ["bogus_metric",]
        assert not result.get('errors')