
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
from graphql_api import data_s3
from graphql_relay import from_global_id, to_global_id

from graphql_api.schema import root_schema
from graphql_api.schema.custom import StrongMotionStation
from graphql_api.schema.custom.sms_file_link import SmsFileLink, SmsFileLinkConnection, CreateSmsFileLink, SmsFileType

import graphql_api.data_s3 # for mocking


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

@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', lambda self: 10)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
@mock.patch('graphql_api.data_s3.BaseS3Data._read_object', lambda self, object_id: mock_file_data)
@mock.patch('graphql_api.data_s3.thing_data.ThingData._read_object', lambda self, object_id: mock_thing_data)
class TestCreateSMSFileLink(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE,
            variable_values=dict(sms_id="U3Ryb25nTW90aW9uU3RhdGlvbjow", file_id="RmlsZToxMA==", file_type="DOWN_HOLE"))
        print(executed)
        new_id =  executed['data']['create_sms_file_link']['sms_file_link']['id']

        # assert new_id == 'U21zRmlsZUxpbms6MA=='
        _type, _id = from_global_id(new_id)
        assert _type == 'SmsFileLink'
        assert _id == '10'