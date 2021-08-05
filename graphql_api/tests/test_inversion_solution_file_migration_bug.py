
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
from graphql_api import data_s3

from graphql_api.schema import root_schema
from graphql_api.schema.custom.inversion_solution import InversionSolution, CreateInversionSolution

import graphql_api.data_s3 # for mocking

READ_MOCK = lambda _self, id: {
  "id": "1233.0nAmGD",
  "file_name": "SOLUTION_FILE_25333.zip",
  "md5_digest": "lEeGRoOtEQcmzLey4ifDJg==",
  "file_size": 9624411,
  "file_url": None,
  "post_url": None,
  "meta": [{"k": "rupture_set", "v": "/home/chrisch/NSHM/opensha-new/work/save/RupSet_Az_FM(CFM_0_9_SANSTVZ_D90)_mxSbScLn(0.5)_mxAzCh(60.0)_mxCmAzCh(560.0)_mxJpDs(5.0)_mxTtAzCh(60.0)_thFc(0.0).zip"}, {"k": "completion_energy", "v": "0.1"}, {"k": "max_inversion_time", "v": "0.5"}, {"k": "scaling_relationship", "v": "TMG_CRU_2017"}], "relations": ["1390pTnrz"],
  "clazz_name": "File",
  "tables": [{"label": "Gridded Hazard 0.25", "table_id": "VGFibGU6OGYyZE5Q", "identity": "0abf8516-fe56-4df5-abf6-d90dcda71365", "created": "2021-08-05T04:54:17.635764+00:00"}]
  }

class TestBugReproduction(unittest.TestCase):
    """
    This occurs in test when trying to use an old (pre InversionSolution)
     as Hasard Report Input from runzi script: inversion_hazard_report_task.py

    raises gql.error.located_error.GraphQLLocatedError: 'tables' is an invalid keyword argument for File
    """
    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_rgt_files(self):
        QRY = '''
          query one_IS ($_id:ID!) {
            node(id: $_id) {
              __typename
              id
            }
          }
        '''
        result = self.client.execute(QRY, variable_values=dict(_id="SW52ZXJzaW9uU29sdXRpb246MTIzMy4wbkFtR0Q="))
        print(result)
        assert result['data']['node']['id'] == "SW52ZXJzaW9uU29sdXRpb246MTIzMy4wbkFtR0Q="
