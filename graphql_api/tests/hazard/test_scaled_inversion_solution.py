import datetime as dt
import unittest
import boto3
import json
from io import BytesIO

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb2, mock_s3
from moto.core import patch_client, patch_resource
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.data import data_manager
from graphql_api.schema.search_manager import SearchManager
from graphql_api.schema.custom.common import TaskSubType

#from graphql_api.data.thing_data import ThingData

class SetupHelpersMixin:
    def create_general_task(self):
        CREATE_QRY = '''
            mutation {
              create_general_task(input: {
                  agent_name:"XOXO"
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
        result = self.client.execute(CREATE_QRY)
        print(result)
        return result['data']['create_general_task']['general_task']['id']


    def create_source_solution(self):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $produced_by: ID!) {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by_id: $produced_by
                  metrics: [{k: "some_metric", v: "20"}]
                  created: "2021-06-11T02:37:26.009506Z"
                  }
              ) {
              inversion_solution { id }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID"))

        print(result)
        return result['data']['create_inversion_solution']['inversion_solution']['id']

    def create_automation_task(self, task_type="INVERSION"):
        CREATE_QRY = '''
            mutation ($created: DateTime! $task_type: TaskSubType!) {
                create_automation_task(input: {
                    task_type: $task_type
                    state: STARTED
                    result: UNDEFINED
                    created: $created
                    duration: 600

                    arguments: [
                        { k:"rates_scalar" v: "0.5" }
                    ]

                    }
                    )
                    {
                        task_result {
                        id
                        task_type
                        created
                        duration
                        arguments {k v}
                    }
                }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(
                task_type = task_type,
                created="2021-06-11T02:37:26.009506Z", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID"))

        print(result)
        return result['data']['create_automation_task']['task_result']['id']


    def create_gt_relation(self, parent_id, child_id):
        CREATE_QRY = '''
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
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(parent_id=parent_id, child_id=child_id))
        print(result)
        return result['data']['create_task_relation']['thing_relation']

    def create_scaled_solution(self):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $file_type: SmsFileType!) {
              create_scaled_inversion_solution(
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  file_type: $file_type
              )
              {
                ok
                file_result { id, file_name, file_size, md5_digest, post_url, file_type}
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size, file_type="DH")

        result = self.client.execute(CREATE_QRY,
            variable_values=variables)
        print(result)
        new_id =  result['data']['create_scaled_inversion_solution']['file_result']['id']

@mock_dynamodb2
@mock_s3
class TestScaling(unittest.TestCase, SetupHelpersMixin):

    def setUp(self):
        self.client = Client(root_schema)

        #S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)

        #Dynamo
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake':'auth'}))

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()

    def test_create_and_scaled_solution_task(self):
        at_id = self.create_automation_task("SCALE_SOLUTION")

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['task_type'],
            TaskSubType.SCALE_SOLUTION.value )

    def test_create_and_link_tasks(self):
        at_id = self.create_automation_task("SCALE_SOLUTION")
        self.create_gt_relation(self.new_gt, at_id)

        self.assertEqual(
            ToshiThingObject.get("100000").object_content['children'][0],
            {'child_clazz': 'AutomationTask', 'child_id': '100001'})

        self.assertEqual(
            ToshiThingObject.get("100001").object_content['parents'][0],
            {'parent_clazz': 'GeneralTask', 'parent_id': '100000'})

    @unittest.skip('TODO')
    def test_create_scaled_solution(self):
        sid = self.create_scaled_solution()

    # def test_complete_tas(self):
    #     at_id = self.create_automation_task()
    #     self.create_gt_relation(self.new_gt, at_id)

