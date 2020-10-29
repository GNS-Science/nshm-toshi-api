import unittest
from graphene.test import Client
from unittest import mock

from graphql_api.schema import schema, OpenshaRuptureGenResult
from graphql_api import data_s3
from io import StringIO, BytesIO     


import botocore
from botocore.exceptions import ClientError

import boto3

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

class TestRuptureGeneratorResults(unittest.TestCase):

    def setUp(self):
        self.client = Client(schema)
        self.mock_all = lambda x : [OpenshaRuptureGenResult(id="0"), OpenshaRuptureGenResult(id="1")]

    def tearDown(self):
        pass
    
    #@unittest.skip("refactoring")
    def test_get_all(self):
        qry = '''
            query { ruptureGeneratorResults {
              edges {
                task: node {
                  id        
                }
              }
            }}'''
        
        with mock.patch('graphql_api.data_s3.BaseS3Data.get_all', new=self.mock_all):
            executed = self.client.execute(qry)
            print(executed)
            assert len( executed['data']['ruptureGeneratorResults']['edges']) == 2


class TestCreateDataFile(unittest.TestCase):

    def setUp(self):
        #data.setup()
        self.client = Client(schema)
        self.mock_all = lambda x : []
        self.mock_create = lambda x, y, **z : None

    def test_upload(self):
        qry = '''
            mutation ($file: Upload!, $digest: String!, $file_name: String!, $file_size: Int!) {
              createDataFile(
                  fileIn: $file
                  hexDigest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) { ok}
            }'''
        
        from hashlib import sha256
        
        filedata = BytesIO("a line\nor two".encode())
        digest = sha256(filedata.read()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size)

        def mock_make_api_call(self, operation_name, kwarg):
            if operation_name in ['ListObjects', 'PutObject']:
                return {}
            raise ValueError("got unmocked operation: ", operation_name)

        with mock.patch('graphql_api.data_s3.BaseS3Data.get_all', new=self.mock_all):
            with mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
                #with mock.patch('graphql_api.data_s3.DataFileData.create', new=self.mock_create):
                executed = self.client.execute(qry, variable_values=variables)
                print(executed)
                assert executed['data']['createDataFile']['ok'] == True

 








        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()