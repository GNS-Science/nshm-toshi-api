
"""
Test API function for SMS

Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data
from graphql_relay import from_global_id, to_global_id

from graphql_api.schema import root_schema
from graphql_api.schema.custom import StrongMotionStation
# from graphql_api.schema.custom.sms_file_link import SmsFileLink #, SmsFileLinkConnection, CreateSmsFileLink, SmsFileType

import graphql_api.data # for mocking


# CREATE = '''
#     mutation (
#         $sms_id: ID!
#         $file_id: ID!
#         $file_type: SmsFileType!
#     ) {
#         create_sms_file_link(
#             sms_id: $sms_id
#             file_id: $file_id
#             file_type: $file_type
#         )
#             {
#                 sms_file_link {
#                     id
#                     file {id, file_name}
#                     thing {
#                       ... on StrongMotionStation {
#                         id
#                       }
#                     }
#             }
#         }
#     }
# '''
mock_file_data = dict(id=10, file_name="a", md5_digest="ca")
mock_thing_data = dict(id=13, clazz_name='StrongMotionStation')

def mock_make_api_call(self, operation_name, kwarg):
    if operation_name in ['ListObjects', 'PutObject']:
        return {}
    raise ValueError("got unmocked operation: ", operation_name)

@mock.patch('graphql_api.data.file_data.FileData.get_next_id', lambda self: "10abcdefgh")
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
@mock.patch('graphql_api.data.BaseDynamoDBData._read_object', lambda self, object_id: mock_file_data)
@mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call)
class TestCreateSMSFile(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):

        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $file_type: SmsFileType!) {
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
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size, file_type="DH")

        executed = self.client.execute(qry,
            variable_values=variables)
        print(executed)
        new_id =  executed['data']['create_sms_file']['file_result']['id']

        #assert new_id == 'U21zRmlsZUxpbms6MA=='
        _type, _id = from_global_id(new_id)
        assert _type == 'SmsFile'
        assert _id == "10abcdefgh"
        assert executed['data']['create_sms_file']['file_result']['file_type'] == 'DH'


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 10)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, body: None)
@mock.patch('graphql_api.data.BaseDynamoDBData._read_object', lambda self, object_id: mock_file_data)
@mock.patch('graphql_api.data.thing_data.ThingData._read_object', lambda self, object_id: mock_thing_data)
class TestCreateSMSFileLink(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    # def test_create_minimum_fields_happy_case(self):
    #     executed = self.client.execute(CREATE,
    #         variable_values=dict(sms_id="U3Ryb25nTW90aW9uU3RhdGlvbjow", file_id="RmlsZToxMA==", file_type="DH"))
    #     print(executed)
    #     new_id =  executed['data']['create_sms_file_link']['sms_file_link']['id']

    #     # assert new_id == 'U21zRmlsZUxpbms6MA=='
    #     _type, _id = from_global_id(new_id)
    #     assert _type == 'SmsFileLink'
    #     assert _id == '10'