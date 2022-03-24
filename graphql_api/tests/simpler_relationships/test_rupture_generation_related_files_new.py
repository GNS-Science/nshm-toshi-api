
"""
Test API function for opensha Rupture Generation related files

Mocking our data layer

"""
import unittest
from copy import copy

from unittest import mock
from graphene.test import Client
from graphql_api.schema import root_schema

GENTASK = {
    "id": "0zHJ450",
    "clazz_name": "RuptureGenerationTask",
    #"created": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "arguments": None, "metrics": None,
    "files": [{"file_id": "0.0mqc7f", "file_role":"write"}],
    }

FILE = {
    "id": "0.0mqc7f", "file_name": "myfile2.txt",
    "md5_digest": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjFIR0FxOA==",
    "file_size": 2000, "file_url": None, "post_url": None,
    "meta": [{"k": "encoding", "v": "utf8"}],
    "relations": [], "clazz_name": "File"}

class TestGetGenerationTaskFiles(unittest.TestCase):


    def setUp(self):
        self.client = Client(root_schema)

    # Note order of calls must match those made to S3 , and copy is used since the object may be mutated
    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object',
        side_effect = [copy(GENTASK), copy(FILE)])
    def test_query_with_files(self, mocked_api):

        qry = '''
        query q1 {
            node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA=") {
            __typename

            ... on RuptureGenerationTask {
                id
                result
                state
                arguments {k v}
                files {
                 total_count
                 edges {

                    node {
                      __typename
                      ... on FileRelation {
                        role
                        file {
                          ... on File {
                            id
                            file_name
                            file_size
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
        }
        '''
        print(qry)
        executed = self.client.execute(qry)
        print(executed)


        result = executed['data']['node']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA='
        assert result['files']['total_count'] == 1
        assert result['files']['edges'][0]['node']['file']['file_name'] == 'myfile2.txt'

        assert mocked_api.call_count == 2
        # this may break id caching or other optimisitions are introduced
