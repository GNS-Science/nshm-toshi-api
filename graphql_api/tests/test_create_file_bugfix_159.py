import unittest
from unittest import mock
from graphene.test import Client
from graphql_api.schema import root_schema
import datetime as dt
from dateutil.tz import tzutc


QUERY_CREATE_FILE_BIG_INT = '''mutation new_rupt_file {
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
    
QUERY_CREATE_FILE_FLOAT = '''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: 30.56
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

QUERY_CREATE_FILE_INT = '''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: 3056
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

QUERY_CREATE_FILE_STRING = '''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: "3056"
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
  def test_create_file_big_int(self):
    result = self.client.execute(QUERY_CREATE_FILE_BIG_INT)
    print(result)
    
    assert result['data']['create_file']['file_result']['id'] == 'RmlsZTpOb25l'
    
  @mock.patch('graphql_api.data.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})  
  def test_create_file_float(self):
    result = self.client.execute(QUERY_CREATE_FILE_FLOAT)
    print(result)
    
    assert result['errors'][0]['message'] == 'Argument "file_size" has invalid value 30.56.\nExpected type "BigInt", found 30.56.'
  
  @mock.patch('graphql_api.data.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})  
  def test_create_file_int(self):
    result = self.client.execute(QUERY_CREATE_FILE_INT)
    print(result)
    
    assert result['data']['create_file']['file_result']['id'] == 'RmlsZTpOb25l'
    
  @mock.patch('graphql_api.data.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})    
  def test_create_file_float(self):
    result = self.client.execute(QUERY_CREATE_FILE_STRING)
    print(result)
    
    assert result['errors'][0]['message'] == 'Argument "file_size" has invalid value "3056".\nExpected type "BigInt", found "3056".'