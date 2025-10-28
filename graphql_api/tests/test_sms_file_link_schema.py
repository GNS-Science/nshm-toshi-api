"""
Test API function for SMS

Mocking our data layer

"""

import unittest
from io import BytesIO
from unittest import mock

import boto3
from graphene.test import Client
from graphql_relay import from_global_id
from moto import mock_dynamodb, mock_s3

import graphql_api.data  # for mocking
from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

# from graphql_api.schema.custom.sms_file_link import SmsFileLink #, SmsFileLinkConnection, CreateSmsFileLink, SmsFileType


CREATE = '''
    mutation (
        $sms_id: ID!
        $file_id: ID!
        $file_type: SmsFileType!
    ) {
        create_sms_file_link(
            sms_id: $sms_id
            file_id: $file_id
            file_type: $file_type
        )
            {
                sms_file_link {
                    id
                    file {id, file_name}
                    thing {
                      ... on StrongMotionStation {
                        id
                      }
                    }
            }
        }
    }
'''
mock_file_data = dict(id=10, file_name="a", md5_digest="ca")
mock_thing_data = dict(id=13, clazz_name='StrongMotionStation')


def mock_make_api_call(self, operation_name, kwarg):
    if operation_name in ['ListObjects', 'PutObject']:
        return {}
    raise ValueError("got unmocked operation: ", operation_name)


# @mock.patch('graphql_api.data.file_data.FileData.get_next_id', lambda self: "10abcdefgh")
# @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
# @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', lambda self, object_id: mock_file_data)
# @mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call)


@mock_s3
@mock_dynamodb
class TestCreateSMSFile(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)
        s3_conn = boto3.resource('s3', region_name=REGION)
        s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))
        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

    def test_create_minimum_fields_happy_case(self):
        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!, $file_type: SmsFileType!) {
              create_sms_file(
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  file_type: $file_type
              ) {
              ok
              file_result { id, file_name, file_size, md5_digest, post_url, file_type}
              }
            }'''

        # from hashlib import sha256, md5

        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size, file_type="DH")

        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        new_id = executed['data']['create_sms_file']['file_result']['id']

        # assert new_id == 'U21zRmlsZUxpbms6MA=='
        _type, _id = from_global_id(new_id)
        assert _type == 'SmsFile'
        assert _id == "100000"
        assert executed['data']['create_sms_file']['file_result']['file_type'] == 'DH'


# @mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 10)
# @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, body: None)
# @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', lambda self, object_id: mock_file_data)
# @mock.patch('graphql_api.data.thing_data.ThingData._read_object', lambda self, object_id: mock_thing_data)

# @mock_s3
# @mock_dynamodb
# class TestCreateSMSFileLink(unittest.TestCase):
#     """
#     All datastore (data) methods are mocked.
#     """
#     def setUp(self):
#         self.client = Client(root_schema)
#         s3_conn = boto3.resource('s3', region_name=REGION)
#         s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
#         self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))
#         ToshiThingObject.create_table()
#         ToshiFileObject.create_table()
#         ToshiIdentity.create_table()

#     def test_create_minimum_fields_happy_case(self):


#                 # at1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
#         # at1.create(
#         #     clazz_name='AutomationTask', created=dt.datetime.now(tzutc())
#         # )  # will get identity 100000 = 'QXV0b21hdGlvblRhc2s6MTAwMDAw',
#         executed = self.client.execute(CREATE,
#             variable_values=dict(sms_id="U3Ryb25nTW90aW9uU3RhdGlvbjow", file_id="RmlsZToxMA==", file_type="DH"))
#         print(executed)
#         new_id =  executed['data']['create_sms_file_link']['sms_file_link']['id']

#         # assert new_id == 'U21zRmlsZUxpbms6MA=='
#         _type, _id = from_global_id(new_id)
#         assert _type == 'SmsFileLink'
#         assert _id == '10'
