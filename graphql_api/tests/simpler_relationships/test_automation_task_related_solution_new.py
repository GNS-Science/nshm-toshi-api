"""
Test API function for opensha AutomationTask & related InversionSolution files

Mocking our data layer

"""

import unittest
from copy import copy
from unittest import mock

from graphene.test import Client

from graphql_api.schema import root_schema

AUTO_TASK = {
    "id": "0zHJ450",
    "clazz_name": "AutomationTask",
    # "created": "2020-10-30T09:15:00+00:00",
    "task_type": "inversion",
    "duration": 600.0,
    "arguments": None,
    "metrics": None,
    "files": [{"file_id": "0.0mqc7f", "file_role": "write"}],
}

FILE0 = {
    "id": "0.0mqc7f",
    "file_name": "solution.zip",
    "md5_digest": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjFIR0FxOA==",
    "file_size": 2000,
    "file_url": None,
    "post_url": None,
    "meta": [{"k": "encoding", "v": "utf8"}],
    "relations": [
        "0V437F",
    ],
    "clazz_name": "InversionSolution",
}

FILE1 = {
    "id": "1.1abchg",
    "file_name": "some_log.log",
    "md5_digest": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjFIR0FxOA==",
    "file_size": 2000,
    "file_url": None,
    "post_url": None,
    "relations": [
        "0V437F",
    ],
    "clazz_name": "File",
}


class TestGetAutomationTaskFiles(unittest.TestCase):
    def setUp(self):
        self.client = Client(root_schema)

    # Note order of calls must match those made to S3 , and copy is used since the object may be mutated
    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', side_effect=[copy(AUTO_TASK), copy(FILE0)])
    def test_query_with_files(self, mocked_api):
        qry = '''
        query q1 {
            node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA=") {
            __typename

            ... on AutomationTask {
                id
                files {
                 total_count
                 edges {
                    node {
                      __typename
                      ... on FileRelation {
                        role
                        file {
                          ... on InversionSolution {
                            id
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
        # print("RESULT", result )
        assert result['id'] == 'QXV0b21hdGlvblRhc2s6MHpISjQ1MA=='
        assert result['files']['total_count'] == 1
        assert result['files']['edges'][0]['node']['file']['id'] == 'SW52ZXJzaW9uU29sdXRpb246MC4wbXFjN2Y='

        assert mocked_api.call_count == 2  # was 3 pre file_relation optimisation

    @mock.patch(
        'graphql_api.data.BaseDynamoDBData._read_object',
        side_effect=[copy(AUTO_TASK), copy(FILE0), copy(AUTO_TASK), None],
    )
    def test_task_product_query(self, mocked_api):
        qry = '''
        query q0 {
          nodes(id_in: ["UnVwdHVyZUdlbmVyYXRpb25UYXNrOjB6SEo0NTA="]) {
            ok
            result {
              edges {
                node {
                  __typename
                  ... on AutomationTask {
                    id
                    created
                    inversion_solution {
                        ... on Node { id }
                        ... on FileInterface { file_name }
                    }
                    files {
                      total_count
                    }
                  }
                }
              }
            }
          }
        }'''

        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        node = executed['data']['nodes']['result']['edges'][0]['node']
        assert node['id'] == 'QXV0b21hdGlvblRhc2s6MHpISjQ1MA=='
        assert node['files']['total_count'] == 1
        assert node['inversion_solution']['id'] == "SW52ZXJzaW9uU29sdXRpb246MC4wbXFjN2Y="
        assert node['inversion_solution']['file_name'] == "solution.zip"

        assert mocked_api.call_count == 2  # this may break if caching or other optimisitions are introduced
