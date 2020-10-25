import unittest
from graphene.test import Client

from graphql_api.schema import schema
from graphql_api import data
from io import StringIO, BytesIO     

class TestTosh(unittest.TestCase):


    def setUp(self):
        data.setup()
        self.client = Client(schema)

    def tearDown(self):
        pass

    def test_get_toshs(self):
        qry = '''
            query { toshs {
              edges {
                task: node {
                  id
                  name        
                }
              }
            }}'''
        
        executed = self.client.execute(qry)
        assert len( executed['data']['toshs']['edges']) == len(data.get_toshs())

class TestToshUpload(unittest.TestCase):

    def setUp(self):
        data.setup()
        self.client = Client(schema)
        self.stringFile = StringIO("""a line\nor two""")
        self.binaryFile = BytesIO("1 3\n 4.5 8".encode())


    def test_text_upload(self):
        qry = '''
            mutation m1 ($file: Upload!) {
              myUpload(fileIn: $file) { ok}
            }'''
        variables = {"file": self.stringFile}
        
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        assert executed['data']['myUpload']['ok'] == True
        #assert False
        
    def test_binary_upload(self):
        qry = '''
            mutation m1 ($file: Upload!) {
              myUpload(fileIn: $file) { ok}
            }'''
        variables = {"file": self.binaryFile}
        
        executed = self.client.execute(qry, variable_values=variables)
        print(executed)
        assert executed['data']['myUpload']['ok'] == True

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()