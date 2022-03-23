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
#from graphql_api.schema.search_manager import SearchManager
#from graphql_api.data.thing_data import ThingData

@mock_dynamodb2
@mock_s3
class TestScaling(unittest.TestCase):

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

    def setUp(self):
        self.client = Client(root_schema)

        #S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)
        #self._bucket = self._s3.Bucket(S3_BUCKET_NAME)

        # self._bucket.put_object(Key='FileData/1587.0nVoFt/object.json', Body=json.dumps(dict(hello='world')))

        #Dynamo
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake':'auth'}))

        self.new_gt = self.create_general_task()
        self.source_solution = self.create_source_solution()

        # gt2 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        # gt2.create(clazz_name='GeneralTask',
        #     created=dt.datetime.now(tzutc())
        #     ) #will get identity 100001 = 'QXV0b21hdGlvblRhc2s6MTAwMDAx',

    def test_startup(self):
        assert True

    @unittest.skip('TODO')
    def test_create_at(self):

        # Create a new AT
        at_result = self.client.execute(QRY_CREATE_AUTOMATION_TASK, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(at_result)
        at_id =  at_result['data']['create_automation_task']['task_result']['id']

        assert at_id == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert from_global_id(at_id) == ("AutomationTask", "100001")

    @unittest.skip('TODO')
    def test_create_at_and_link_file(self):

        # Create a new AT
        at_result = self.client.execute(QRY_CREATE_AUTOMATION_TASK, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(at_result)
        at_id =  at_result['data']['create_automation_task']['task_result']['id']

        # assert at_id == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        # assert from_global_id(at_id) == ("AutomationTask", "100001")

        file_id = to_global_id(FILEMOCK['clazz_name'], FILEMOCK['id'] )

        # the relation
        link_result = self.client.execute(QRY_CREATE_AT_RELATION, variable_values=dict(
            thing_id=at_id,
            file_id=file_id))

        assert link_result['data']['create_file_relation']['ok'] == True
