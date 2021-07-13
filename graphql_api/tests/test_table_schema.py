
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

class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return str(self.next_id) + 'RANDM'

TABLEMOCK = lambda _self, _id: {
    "id": "0i93qK", "created": "2021-06-11T02:37:26.009506+00:00",
    "object_id": "R2VuZXJhbFRhc2s6MjE3Qk1YREw=",
    "column_headers": ["OK", "DOKEY"],
    "column_types": ["INT", "DBL"],
    "rows": [["1", "1.01"], ["2", "2.2"]], "clazz_name": "Table"
    }


@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestBasicTableOperations(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', IncrId().get_next_id)
    def test_create_minimal_table(self):
        CREATE_TABLE = '''
            mutation create_Table {
              create_table(input: {
                object_id: "R2VuZXJhbFRhc2s6MjE3Qk1YREw="
                created: "2021-06-11T02:37:26.009506+00:00"
                column_headers: ["OK", "DOKEY"]
                column_types:[ integer, double]
                rows:[["1","1.01"], ["2", "2.2"]]
              })
              {
                table {
                  id
                }
              }
            }
        '''
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

    @mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', IncrId().get_next_id)
    def test_create_bigger_table(self):
        CREATE_TABLE = '''
            mutation create_Table {
              create_table(input: {
                object_id: "R2VuZXJhbFRhc2s6MjE3Qk1YREw="
                created: "2021-06-11T02:37:26.009506+00:00"
                column_headers: ["series", "series_name", "X", "Y"]
                column_types:[integer, string, double, double]
                rows: [
                    ["4", "solutionMFD_rateWeighted", "6.05", "0.03334654109880432"],
                    ["4", "solutionMFD_rateWeighted", "6.15", "0.03002277966581522"],
                    ["4", "solutionMFD_rateWeighted", "6.25", "0.028779972773046576"],
                    ["4", "solutionMFD_rateWeighted", "6.35", "0.030256070931683546"],
                    ["4", "solutionMFD_rateWeighted", "6.45", "0.022814558988582288"],
                    ["4", "solutionMFD_rateWeighted", "6.55", "0.02122819920618953"],
                    ["4", "solutionMFD_rateWeighted", "6.65", "0.018957218632132317"],
                    ["4", "solutionMFD_rateWeighted", "6.75", "0.017530043245039578"],
                    ["4", "solutionMFD_rateWeighted", "6.85", "0.012210047407016639"],
                    ["4", "solutionMFD_rateWeighted", "6.95", "0.010346757371270837"],
                    ["4", "solutionMFD_rateWeighted", "7.05", "0.007878279178202245"],
                    ["4", "solutionMFD_rateWeighted", "7.15", "0.006360355727094245"],
                    ["4", "solutionMFD_rateWeighted", "7.25", "0.00404161655830802"],
                    ["4", "solutionMFD_rateWeighted", "7.35", "0.0040961496788813005"],
                    ["4", "solutionMFD_rateWeighted", "7.45", "0.002032439960143476"],
                    ["4", "solutionMFD_rateWeighted", "7.55", "0.0014745441510661335"],
                    ["4", "solutionMFD_rateWeighted", "7.65", "0.0012815397741464947"],
                    ["4", "solutionMFD_rateWeighted", "7.75", "0.0014055294096273997"],
                    ["4", "solutionMFD_rateWeighted", "7.85", "0.0010879800797796775"],
                    ["4", "solutionMFD_rateWeighted", "7.95", "6.591487929707425E-4"],
                    ["4", "solutionMFD_rateWeighted", "8.05", "3.453383255900045E-5"]
                ]
              })
              {
                table {
                  id
                }
              }
            }
        '''
        # the first GT
        result = self.client.execute(CREATE_TABLE, variable_values={})
        print(result)
        assert result['data']['create_table']['table']['id'] == 'VGFibGU6MFJBTkRN'


