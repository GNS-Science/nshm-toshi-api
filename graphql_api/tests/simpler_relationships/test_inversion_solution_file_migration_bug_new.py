
"""
Test API function for InversionSolution
Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest
import json

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data

import itertools
import copy

from graphql_api.schema import root_schema
from graphql_api.schema.custom.inversion_solution import InversionSolution, CreateInversionSolution

import graphql_api.data # for mocking

FILE = lambda: {
  "id": "1233.0nAmGD",
  "file_name": "SOLUTION_FILE_25333.zip",
  "md5_digest": "lEeGRoOtEQcmzLey4ifDJg==",
  "file_size": 9624411,
  "file_url": None,
  "post_url": None,
  "meta": [{"k": "rupture_set", "v": "/home/chrisch/NSHM/opensha-new/work/save/RupSet_Az_FM(CFM_0_9_SANSTVZ_D90)_mxSbScLn(0.5)_mxAzCh(60.0)_mxCmAzCh(560.0)_mxJpDs(5.0)_mxTtAzCh(60.0)_thFc(0.0).zip"}, {"k": "completion_energy", "v": "0.1"}, {"k": "max_inversion_time", "v": "0.5"}, {"k": "scaling_relationship", "v": "TMG_CRU_2017"}], 
  "clazz_name": "File",
  "tables": [{"label": "Gridded Hazard 0.25", "table_id": "VGFibGU6OGYyZE5Q", "identity": "0abf8516-fe56-4df5-abf6-d90dcda71365", "created": "2021-08-05T04:54:17.635764+00:00"}]
  }

RUPTGEN = lambda: {
  "id": "0zHJ450",
  "clazz_name": "RuptureGenerationTask",
  "files" :[{"file_id": "0.0mqc7f", "file_role":"write"}]
}

ANON = lambda: {"clazz_name": "Anon",}

class TestBugReproduction(unittest.TestCase):
    """
    This occurs in test when trying to use an old (pre InversionSolution)
     as Hazard Report Input from runzi script: inversion_hazard_report_task.py

    raises gql.error.located_error.GraphQLLocatedError: 'tables' is an invalid keyword argument for File
    """
    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseData._read_object', side_effect=[FILE()])
    def test_get_inversion_solution(self, mock):
        QRY = '''
          query one_inversion_solution ($_id:ID!) {
            node(id: $_id) {
              __typename
              id
            }
          }
        '''
        result = self.client.execute(QRY, variable_values=dict(_id="SW52ZXJzaW9uU29sdXRpb246MTIzMy4wbkFtR0Q="))
        print(result)
        assert result['data']['node']['id'] == "SW52ZXJzaW9uU29sdXRpb246MTIzMy4wbkFtR0Q="

    @mock.patch('graphql_api.data.BaseData._read_object', side_effect=itertools.chain([RUPTGEN(), FILE(), RUPTGEN()], itertools.repeat(ANON()))) #, itertools.repeat(copy.copy(FILE)))
    def test_get_ruptgen_files(self, mock):
        QRY = '''
          query one_rgt ($rgt_id:ID!) {
            node(id: $rgt_id) {
              __typename
              ... on RuptureGenerationTask {
                id
                files {
                  total_count
                    edges {
                      node {
                       # id
                        file {
                          ... on InversionSolution {
                            tables {
                              label
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
        '''
        result = self.client.execute(QRY, variable_values=dict(rgt_id="UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA="))
        print(result)
        assert result['data']['node']['id'] == "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA="
        assert result['data']['node']['files']['total_count'] == 1
        assert result['data']['node']['files']['edges'][0]['node']['file']['tables'][0]['label'] == "Gridded Hazard 0.25"

    @mock.patch('graphql_api.data.BaseData._read_object', side_effect=itertools.chain([FILE()], itertools.repeat(ANON()))) #, itertools.repeat(copy.copy(FILE)))
    def test_get_ruptgen_files_with_created_datetime(self, mock):
        QRY = '''
          query inversion_solution_tables {
            node(id:"SW52ZXJzaW9uU29sdXRpb246MTIzMy4wbkFtR0Q=") {
              ... on InversionSolution {
                file_name
                metrics {k v}
                tables {
                  table_id
                  created
                  label
                }
              }
            }
          }
        '''
        result = self.client.execute(QRY)
        print(result)
        assert result['data']['node']['tables'][0]['created'] == "2021-08-05T04:54:17.635764+00:00"