"""
Test schema operations
"""

from io import BytesIO
from unittest import mock

import datetime
import unittest

from dateutil.tz import tzutc

import boto3
import botocore
from botocore.exceptions import ClientError
from graphene.test import Client
from graphql_api import data
from graphql_api.schema import root_schema, RuptureGenerationTask
from graphql_api.dynamodb.models import migrate
from moto import mock_dynamodb



orig = botocore.client.BaseClient._make_api_call

def mock_make_api_call(self, operation_name, kwarg):
    if operation_name == 'UploadPartCopy':
        parsed_response = {'Error': {'Code': '500', 'Message': 'Error Uploading'}}
        raise ClientError(parsed_response, operation_name)
    if operation_name == 'ListObjects':
        return {}
    if operation_name == 'PutObject':
        return {}
    else:
        raise ValueError("mock_call unmocked operation: ", operation_name)
    return orig(self, operation_name, kwarg)

class TestBotoMocked(unittest.TestCase):

    def test_get_new_mocked(self):
        with mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
            client = boto3.client('s3')
            # Should return actual result
            # o = client.get_object(Bucket='my-bucket', Key='my-key')
            # Should return mocked exception
            with self.assertRaises(ClientError):
                e = client.upload_part_copy()

# r0 = {'ResponseMetadata': {
#           'HTTPStatusCode': 200,
#           'HTTPHeaders': {
#               'content-type': 'application/xml',
#               'content-length': '1135',
#               'date': 'Thu, 29 Oct 2020 04:25:42 GMT',
#               'connection': 'keep-alive'},
#           'RetryAttempts': 0},
#           'IsTruncated': False, 'Marker': '',
#      }
r1 = {'Contents': [{
        'Key': 'TaskResultData/0/object.json',
        'LastModified': datetime.datetime(2020, 10, 28, 8, 17, 15, tzinfo=tzutc()),
        'ETag': '"b91ae62013c8beffb0770a8209a0b426"',
        'Size': 240, 'StorageClass': 'STANDARD',
        'Owner': {'DisplayName': 'S3rver', 'ID': '123456789000'}},

        {'Key': 'TaskResultData/1/object.json',
        'LastModified': datetime.datetime(2020, 10, 28, 17, 59, 49, tzinfo=tzutc()),
        'ETag': '"31ca7cb08f8efd26a12c5349bc2c976f"', 'Size': 240,
        'StorageClass': 'STANDARD',
        'Owner': {'DisplayName': 'S3rver', 'ID': '123456789000'}}],
        'Name': 'nshm-tosh-api-test', 'Prefix': 'TaskResultData/', 'MaxKeys': 1000}

r2 = {'ResponseMetadata': {'HTTPStatusCode': 200, 'HTTPHeaders': {'accept-ranges': 'bytes', 'content-type': 'binary/octet-stream', 'last-modified': 'Wed, 28 Oct 2020 08:17:15 GMT', 'etag': '"b91ae62013c8beffb0770a8209a0b426"', 'content-length': '240', 'date': 'Thu, 29 Oct 2020 04:43:48 GMT', 'connection': 'keep-alive'}, 'RetryAttempts': 0},
      'AcceptRanges': 'bytes',
      'LastModified': datetime.datetime(2020, 10, 28, 8, 17, 15, tzinfo=tzutc()),
      'ContentLength': 240,
      'ETag': '"b91ae62013c8beffb0770a8209a0b426"', 'ContentType': 'binary/octet-stream', 'Metadata': {}}

obj3 = b'{"id": "0", "name": null, "tasktype": null, "started": "2020-10-28T09:14:00+00:00", "duration": 600.0, "data_files": null, "rupture_generator_args": {"max_jump_distance": 5.5, "max_sub_section_length": 2.0, "max_cumulative_azimuth": 590.0}}'

r3 = {'ResponseMetadata': {'HTTPStatusCode': 200, 'HTTPHeaders': {'accept-ranges': 'bytes', 'content-type': 'binary/octet-stream', 'last-modified': 'Wed, 28 Oct 2020 08:17:15 GMT', 'etag': '"b91ae62013c8beffb0770a8209a0b426"', 'content-length': '240', 'date': 'Thu, 29 Oct 2020 04:48:40 GMT', 'connection': 'keep-alive'}, 'RetryAttempts': 0}, 'AcceptRanges': 'bytes', 'LastModified': datetime.datetime(2020, 10, 28, 8, 17, 15, tzinfo=tzutc()), 'ContentLength': 240, 'ETag': '"b91ae62013c8beffb0770a8209a0b426"', 'ContentType': 'binary/octet-stream', 'Metadata': {},
      'Body': BytesIO(obj3)}
      # <botocore.response.StreamingBody object at 0x10c255bd0>}
class TestRuptureGeneratorResults(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        self.mock_all = lambda x, y : [RuptureGenerationTask(id="0"), RuptureGenerationTask(id="1")]

    def tearDown(self):
        pass

    #@unittest.skip("refactoring")
    def test_get_all(self):
        qry = '''
            query { rupture_generation_tasks {
              edges {
                task: node {
                  id
                }
              }
            }}'''
        
        def mock_make_api_call(self, operation_name, kwarg):
            if operation_name in ['ListObjects']:
                return r1 #dict(data=dict(rupture_generation_tasks=dict(edges=[0,1])))
            elif operation_name == 'HeadObject':
                return r2
            elif operation_name == 'GetObject':
                return r3
            else:
                print('kwarg', kwarg)
                res = orig(self, operation_name, kwarg)
                print(res)
                raise ValueError("got unmocked operation: ", operation_name)

        with mock.patch('graphql_api.data.BaseDynamoDBData.get_all', new=self.mock_all):
        #with mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
            executed = self.client.execute(qry)
            print(executed)
            print("***")
            # assert 0
            assert len( executed['data']['rupture_generation_tasks']['edges']) == 2

@mock_dynamodb
class TestCreateDataFile(unittest.TestCase):

    def setUp(self):
        #data.setup()
        # migrate()
        self.client = Client(root_schema)
        self.mock_all = lambda x : []
        self.mock_create = lambda x, y, **z : None
    
    @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
    @mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
    # @mock.patch('graphql_api.data.BaseData._read_object', lambda self, object_id: None)
    # @mock.patch('graphql_api.data.BaseDynamoDBData.transact_update', lambda self, object_id, object_type, body: None)
    def test_upload(self):
        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!) {
              create_file(
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
              ) {
              ok
              file_result { id, file_name, file_size, md5_digest, post_url }
              }
            }'''

        # from hashlib import sha256, md5

        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size)

        def mock_make_api_call(self, operation_name, kwarg):
            if operation_name in ['ListObjects', 'PutObject']:
                return {}
            raise ValueError("got unmocked operation: ", operation_name)

        #TODO mock out the presigned URL calls
        with mock.patch('graphql_api.data.BaseData.get_all', new=self.mock_all):
            with mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
                #with mock.patch('graphql_api.data.DataFileData.create', new=self.mock_create):
                executed = self.client.execute(qry, variable_values=variables)
                print(executed)
                assert executed['data']['create_file']['ok'] == True


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()