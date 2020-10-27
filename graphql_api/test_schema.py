import unittest
from graphene.test import Client
from unittest import mock

from graphql_api.schema import schema, OpenshaRuptureGenResult
from graphql_api import data_s3
from io import StringIO, BytesIO     

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
        
        with mock.patch('graphql_api.data_s3.TaskResultData.get_all', new=self.mock_all):
            executed = self.client.execute(qry)
            print(executed)
            assert len( executed['data']['ruptureGeneratorResults']['edges']) == 2


class TestCreateDataFile(unittest.TestCase):

    def setUp(self):
        #data.setup()
        self.client = Client(schema)

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
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        assert executed['data']['createDataFile']['ok'] == True

               
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()