import datetime as dt
import json
import unittest
from copy import copy
from io import BytesIO
from re import S
from unittest import mock
from unittest.case import skip

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

import graphql_api.data
from graphql_api import data
from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.data.thing_data import ThingData
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.custom.general_task import GeneralTask
from graphql_api.schema.search_manager import SearchManager

thing_args = {}

rupt_body = {
    'id': 0,
    'files': None,
    'result': None,
    'state': None,
    'duration': None,
    'parents': None,
    'arguments': None,
    'environment': None,
    'metrics': None,
    'clazz_name': 'RuptureGenerationTask',
}
gen_task_body = {
    "id": 1,
    "updated": None,
    "title": "My First Manual task",
    "description": "##Some notes go here",
    "agent_name": "chrisbc",
}

START_ID = 100000


@mock_dynamodb
class TestTaskTaskRelations(unittest.TestCase):
    def setUp(self):
        self.client = Client(root_schema)
        ToshiThingObject.create_table()
        ToshiIdentity.create_table()
        self._s3 = boto3.resource('s3')
        self._client = boto3.client('s3')
        self._bucket_name = S3_BUCKET_NAME
        self._model = ToshiThingObject()
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))
        self._connection = Connection(region=REGION)

    def test_create_task_task_relations(self):
        general_task = ThingData(thing_args, self._data_manager, ToshiThingObject, self._connection)
        general_task.create(clazz_name='GeneralTask', created=dt.datetime.now(tzutc()))

        rupt_gen_task = ThingData(thing_args, self._data_manager, ToshiThingObject, self._connection)
        rupt_gen_task.create(clazz_name='RuptureGenerationTask', created=dt.datetime.now(tzutc()))

        self._data_manager.thing_relation.create(
            parent_clazz='GeneralTask',
            child_clazz='RuptureGenerationTask',
            parent_id=str(START_ID),
            child_id=str(START_ID + 1),
        )

        print(rupt_gen_task._read_object(str(START_ID + 1)))
        assert rupt_gen_task._read_object(str(START_ID + 1))['id'] == START_ID + 1
        assert rupt_gen_task._read_object(str(START_ID + 1))['clazz_name'] == 'RuptureGenerationTask'
        assert rupt_gen_task._read_object(str(START_ID + 1))['parents'][0]['parent_id'] == str(START_ID)
        assert rupt_gen_task._read_object(str(START_ID + 1))['parents'][0]['parent_clazz'] == 'GeneralTask'

        print(general_task._read_object(str(START_ID)))
        assert general_task._read_object(str(START_ID))['id'] == START_ID
        assert general_task._read_object(str(START_ID))['clazz_name'] == 'GeneralTask'
        assert general_task._read_object(str(START_ID))['children'][0]['child_id'] == str(START_ID + 1)
        assert general_task._read_object(str(START_ID))['children'][0]['child_clazz'] == 'RuptureGenerationTask'
