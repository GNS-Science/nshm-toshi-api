
"""
Test API function for Table
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
from graphql_api.schema.table import Table, CreateTable

import graphql_api.data_s3 # for mocking

CREATE_TABLE = '''
    mutation create_Table {
      create_table(input: {
        object_id: "R2VuZXJhbFRhc2s6MjE3Qk1YREw="
        created: "2021-06-11T02:37:26.009506+00:00"
        column_headers: ["OK", "DOKEY"]
        column_types:[ integer, floating]
        rows:[["1","1.01"], ["2", "2.2"]]
      })
      {
        table {
          id
        }
      }
    }
'''

class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return str(self.next_id) + 'RANDM'

TABLEMOCK = lambda _self, _id: {
    "id": "0i93qK", "created": "2021-06-11T02:37:26.009506+00:00",
    "object_id": "R2VuZXJhbFRhc2s6MjE3Qk1YREw=",
    "column_headers": ["OK", "DOKEY"],
    "column_types": ["INT", "FLOAT"],
    "rows": [["1", "1.01"], ["2", "2.2"]], "clazz_name": "Table"
    }

@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', IncrId().get_next_id)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestBasicTableOperations(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    # @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', TABLEMOCK)
    def test_create_bare_table(self):
        # the first GT
        result = self.client.execute(CREATE_TABLE, variable_values={})
        print(result)
        assert result['data']['create_table']['table']['id'] == 'VGFibGU6MFJBTkRN'


    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', TABLEMOCK)
    def test_get_table_by_node_id(self):
        # the first GT
        qry = '''
        query get_FDT {
          node(id:"VGFibGU6MA==") {
            __typename
            ... on Table {
              created
              id
              object_id
              rows
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'VGFibGU6MGk5M3FL'
        assert result['data']['node']['object_id'] == "R2VuZXJhbFRhc2s6MjE3Qk1YREw="
        assert result['data']['node']['rows'] == [["1", "1.01"], ["2", "2.2"]]
