
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
    argument_lists = [{"k": "bogus_metric", "v": ["20", "25"]}, {"k": "unswept_metric", "v": [None]}],
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
                  general_task { id }
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