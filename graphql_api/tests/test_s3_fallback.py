from graphql_api.schema.search_manager import SearchManager
from re import S
from graphql_api.data import data_manager
from unittest.case import skip
from graphql_api.config import REGION, S3_BUCKET_NAME
from io import BytesIO
from unittest import mock
import json

import datetime as dt
import unittest
from copy import copy
from dateutil.tz import tzutc
import boto3

from graphene.test import Client
from graphql_api import data
from moto import mock_dynamodb2, mock_s3
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject

import graphql_api.data
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.data.thing_data import ThingData

thing_args = {}

body = {'id': 0, 'created': '2022-02-18T00:53:43.934035+00:00', 'files': None, 'result': None, 'state': None, 'duration': None, 'parents': None, 'arguments': None, 'environment': None, 'metrics': None, 'clazz_name': 'RuptureGenerationTask'}

START_ID = 100000

@mock_dynamodb2
class TestS3FallBackRead(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        ToshiThingObject.create_table()
        ToshiIdentity.create_table()
        self._s3 = boto3.resource('s3')
        self._client = boto3.client('s3')
        self._bucket_name = S3_BUCKET_NAME
        self._model = ToshiThingObject()
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake':'auth'}))
        self._connection = Connection(region=REGION)
        

    def test_thing_read_dynamodb(self):
        thing = ThingData(thing_args, self._data_manager, ToshiThingObject, self._connection)
        thing.create(clazz_name='RuptureGenerationTask', created=dt.datetime.now(tzutc()))
        print(thing._read_object(str(START_ID)))
        assert thing._read_object(str(START_ID))['id'] == START_ID
        assert thing._read_object(str(START_ID))['clazz_name'] == 'RuptureGenerationTask'
       
      
    def test_thing_read_s3(self):
        with mock_s3():
            conn = boto3.resource('s3', region_name='us-east-1')
            conn.create_bucket(Bucket=S3_BUCKET_NAME)
            bucket = conn.Bucket(S3_BUCKET_NAME)
            thing = ThingData(thing_args, self._data_manager, ToshiThingObject, self._connection)
            
            self._prefix = 'ThingData'
            object_id = 0
            key = "%s/%s/%s" % (self._prefix, object_id, "object.json")
            
            bucket.put_object(Key=key, Body=json.dumps(body))

            print(thing._read_object('0'))
            assert thing._read_object('0')['id'] == 0
            assert thing._read_object('0')['clazz_name'] == 'RuptureGenerationTask'
