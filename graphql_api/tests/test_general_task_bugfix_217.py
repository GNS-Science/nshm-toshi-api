"""
Test API function for GeneralTask
using moto mocking
"""

import datetime as dt
import json
import unittest
from io import BytesIO

import boto3
import pytest
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

CREATE_GT = '''
    mutation new_gt ($created: DateTime!) {
      create_general_task(input:{
        created: $created
        title: "TEST Build opensha rupture set Coulomb #1"
        description:"Using "
        agent_name:"chrisbc"
        subtask_type: OPENQUAKE_HAZARD,
        model_type: COMPOSITE
        argument_lists: [{k: "some_metric", v: ["20", "25"]}]
      })
      {
        general_task{
          id
          subtask_type
          model_type
        }
      }
    }
'''


@mock_s3
@mock_dynamodb
class TestGeneralTaskBug217(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        # migrate()

        self._s3_conn = boto3.resource('s3', region_name=REGION)
        self._s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3_conn.Bucket(S3_BUCKET_NAME)
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))

    def test_create_one_gt(self):

        gt1_result = self.client.execute(CREATE_GT, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(gt1_result)
        assert gt1_result['data']['create_general_task']['general_task']['id'] == 'R2VuZXJhbFRhc2s6MTAwMDAw'
        assert gt1_result['data']['create_general_task']['general_task']['subtask_type'] == 'OPENQUAKE_HAZARD'
        assert gt1_result['data']['create_general_task']['general_task']['model_type'] == 'COMPOSITE'
