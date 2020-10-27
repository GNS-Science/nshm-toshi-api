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

    def test_text_upload(self):
        qry = '''
            mutation ($file: Upload!) {
              createDataFile(fileIn: $file) { ok}
            }'''
        variables = {"file": StringIO("""a line\nor two""")}
        
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        assert executed['data']['createDataFile']['ok'] == True
               
    def test_binary_upload(self):
        qry = '''
            mutation m1 ($file: Upload!) {
              createDataFile(fileIn: $file) { ok}
            }'''
        variables = {"file": BytesIO("1 3\n 4.5 8".encode())}
        
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        assert executed['data']['createDataFile']['ok'] == True
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()