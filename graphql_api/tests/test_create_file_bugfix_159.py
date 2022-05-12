import unittest
from unittest import mock
from graphene.test import Client
from graphql_api.schema import root_schema
import datetime as dt
from dateutil.tz import tzutc


QUERY_CREATE_FILE = '''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: 3056707615
        md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        meta: [{ k:"encoding" v:"utf8"}]
        ) {
            ok
            file_result {
              id
              file_size
              meta {k v}
            }
        }
    }'''
    

class TestCreateFileBug159(unittest.TestCase):
  
  def setUp(self):
    self.client = Client(root_schema)
    
  @mock.patch('graphql_api.data.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})  
  def test_create_file(self):
    result = self.client.execute(QUERY_CREATE_FILE)
    print(result)
    
    assert result['data']['create_file']['file_result']['id'] == 'RmlsZTpOb25l'