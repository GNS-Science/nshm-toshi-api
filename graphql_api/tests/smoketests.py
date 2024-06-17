"""
Run all these queries manually in sequence  to validate current behaviour.

Some duplication in existing tests, but not everything.

Setup:
 - docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
 - rm -R /tmp/nshm-toshi-api-local/*
 - sls dynamodb start --stage local & sls s3 start & SLS_OFFLINE=1 TOSHI_FIX_RANDOM_SEED=1 sls wsgi serve

now python3 smoketests.py
"""

import os
import time

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# from graphql_api.dynamodb.models import drop_tables


api_url = os.getenv('TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
auth_token = os.getenv('TOSHI_API_KEY', "")


class SmokeTest:
    def __init__(self, query, expected, query_fragment=None):
        self.query = query
        self.expected = expected
        self.query_fragment = query_fragment

        headers = {"Authorization": "Bearer %s" % auth_token}
        headers = {"x-api-key": auth_token}
        transport = RequestsHTTPTransport(url=api_url, headers=headers, use_json=True)

        self._client = Client(transport=transport, fetch_schema_from_transport=True)

    def execute(self):
        qry = self.query
        if self.query_fragment:
            qry = self.query_fragment + '\n\n' + self.query

        response = 'Didnt run'

        try:
            gql_query = gql(qry)
            # self._client.validate(gql_query)
            response = self._client.execute(gql_query)
        except Exception as e:
            print(e)
            raise

        # print(response)

        if not response == self.expected:
            print("query", qry)
            print()
            print("expected", self.expected)
            print()
            print('response', response)
            assert 0


test_setup = [
    '''mutation new_sms {
      create_strong_motion_station (input: {
        site_code: "ABCD"
        created: "2020-10-10T23:00Z"
        site_class_basis:SPT
        Vs30_mean:[200.0,]
        site_class:B
      }) {
        strong_motion_station {
          id
        }
      }
    }''',
    '''mutation new_ruptgen_task {
      create_rupture_generation_task(input:{
        created:"2020-10-10T23:00Z"
        state:SCHEDULED
        result: UNDEFINED
      }) {
        task_result {
          id
          created
        }
      }
    }''',
    '''mutation update_ruptgen_task {
      update_rupture_generation_task(input: {
        task_id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        result:SUCCESS
        state:DONE
      })
      {
        task_result {
          id
        }
      }
    }''',
    '''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: 2000
        md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        meta: [{ k:"encoding" v:"utf8"}]
        ) {
            file_result {
              id
              meta {k v}
            }
        }
    }''',
    '''mutation new_rupt_file_relation {
        create_file_relation(
          file_id: "RmlsZTow"
          thing_id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
          role: WRITE
        ) {
          ok
        }
    }''',
    '''mutation new_sms_file {
        create_sms_file(file_name:"my_sms_File2.txt"
        file_size: 2000
        file_type: CPT
        md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
            file_result {
              id
              file_type
            }
        }
    }''',
    '''mutation new_sms_file_relation {
      create_file_relation(
        file_id: "U21zRmlsZTox"
        thing_id:"U3Ryb25nTW90aW9uU3RhdGlvbjow"
        role: UNDEFINED
      ) {
        ok
      }
    }''',
    '''mutation new_general_task {
      create_general_task(input: {
        created: "2020-10-10T23:00:00+00:00"
        title: "My First Manual task"
        description: "##Some notes go here"
        agent_name: "chrisbc"
      }) {
        general_task {
          created
        }
      }
    }''',
    '''mutation new_gt_file_relation {
      create_file_relation(
        file_id: "RmlsZTow"
        thing_id: "R2VuZXJhbFRhc2s6Mg=="
        role:READ
      ) {
        ok
      }
    }''',
    '''mutation new_gt_smsfile_relation {
      create_file_relation(
        file_id: "U21zRmlsZTox"
        thing_id: "R2VuZXJhbFRhc2s6Mg=="
        role:UNDEFINED
      ) {
        ok
      }
    }''',
    '''mutation new_task_subtask_relation {
      create_task_relation(
        child_id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        parent_id: "R2VuZXJhbFRhc2s6Mg==")
      {thing_relation {
          parent {
            ... on GeneralTask {id}
          }
          child {
            ... on RuptureGenerationTask{id}
          }
      }
      }
    }''',
    '''mutation new_inversion {
      create_automation_task (input:{
          task_type:INVERSION
          result:UNDEFINED
          state:UNDEFINED
          created:"2020-10-10T23:00Z"
          arguments: [
              { k:"max_jump_distance" v: "55.5" }
          ]

          environment: [
              { k:"gitref_opensha_ucerf3" v: "ABC"}
              { k:"JAVA" v:"-Xmx24G"  }
          ]

        }) {
        task_result {
          id
          created
          arguments {k v}
          }
        }
      }''',
    '''
    mutation new_ruptgen_new_task {
        create_rupture_generation_task(input: {
            state: UNDEFINED
            result: UNDEFINED
            created: "2020-10-10T23:00Z"
            duration: 600
            arguments: [
                { k:"max_jump_distance" v: "55.5" }
                { k:"max_sub_section_length" v: "2" }
                { k:"max_cumulative_azimuth" v: "590" }
                { k:"min_sub_sections_per_parent" v: "2" }
                { k:"permutation_strategy" v: "DOWNDIP" }
            ]
          environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"gitref_opensha_commons" v: "ABC"}
                { k:"gitref_opensha_core" v: "ABC"}
                { k:"nshm_nz_opensha" v: "ABC"}
                { k:"host" v:"tryharder-ubuntu"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

          metrics: [
            { k:"subsection_count" v:"3600"}
            { k:"total_energy" v:"3280.2333"}
          ]
          })
          {
              task_result {
              id
              created
              duration
              arguments {k v}
          }
        }
    }
    ''',
]

search_fragments = '''
fragment sr on SearchResult {
  __typename
  ... on File {
    id
    file_name
    relations {
      edges {
        node {
          ... on FileRelation {
            role
            thing {
              __typename
              ... on RuptureGenerationTask {
                created

              }
            }
          }
        }
      }
    }
  }
  ... on SmsFile {
    id
    file_name
    file_type
    relations {
      edges {
        node {
          __typename
          ... on FileRelation {
            role
            thing {
              __typename
              ... on StrongMotionStation {
                site_code
              }
            }
          }
        }
      }
    }
  }
  ... on RuptureGenerationTask {
    id
    result
    state
    args: arguments {k v}
    files {
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
  ... on StrongMotionStation {
    id
    created
    site_code
    site_class
    site_class_basis
    liquefiable
    Vs30_mean
    files {
      edges {
        node {
          __typename
          ... on FileRelation {
            role
            file {
              ... on SmsFile {
                file_name
                file_size
              }
            }
          }
        }
      }
    }
  }
  ... on GeneralTask {
    id
    created
    updated
    title
    description
    agent_name

    children {
      edges {
        node {
          child {
            __typename
            ... on RuptureGenerationTask {
              id
              state
              result
              created
            }
          }
        }
      }
    }

    files {
     edges {
        node {
          __typename
          ... on FileRelation {
            role
            file {
              __typename
              __typename
              ... on Node {
                id
              }
              ... on File {
                file_name
                file_size
              }
              ... on SmsFile {
                file_name
                file_size
                file_type
              }
            }
          }
        }
      }
    }
  }

  ... on AutomationTask {
    id
    created
    task_type
    args_at: arguments {k v}
  }
}
'''

smoketests = [
    SmokeTest(
        query='''query search_sms {
      search(
        search_term: "site_class_basis:SPT&size=20&sort=created:asc"
      ) {
        search_result {
          edges {
            node {
              ...sr
            }
          }
        }
      }
    }''',
        expected={
            'search': {
                'search_result': {
                    'edges': [
                        {
                            'node': {
                                '__typename': 'StrongMotionStation',
                                'id': 'U3Ryb25nTW90aW9uU3RhdGlvbjow',
                                'created': '2020-10-10T23:00:00+00:00',
                                'site_code': 'ABCD',
                                'site_class': 'B',
                                'site_class_basis': 'SPT',
                                'liquefiable': None,
                                'Vs30_mean': [200.0],
                                'files': {
                                    'edges': [
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'UNDEFINED',
                                                'file': {'file_name': 'my_sms_File2.txt', 'file_size': 2000},
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                    ]
                }
            }
        },
        query_fragment=search_fragments,
    ),
    SmokeTest(
        query='''query search_rupture {
      search(
        search_term: "result:SUCCESS"
        #search_term: "file_name: myfile*"
        #search_term: "id: UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
      ) {
        search_result {
          edges {
            node {
              ...sr
            }
          }
        }
      }
    }''',
        expected={
            'search': {
                'search_result': {
                    'edges': [
                        {
                            'node': {
                                '__typename': 'RuptureGenerationTask',
                                'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=',
                                'result': 'SUCCESS',
                                'state': 'DONE',
                                'args': None,
                                'files': {
                                    'edges': [
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'WRITE',
                                                'file': {
                                                    'id': 'RmlsZTow',
                                                    'file_name': 'myfile2.txt',
                                                    'file_size': 2000,
                                                },
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                    ]
                }
            }
        },
        query_fragment=search_fragments,
    ),
    SmokeTest(
        query='''query search_file {
      search(
        search_term: "file_name:my_sms*"
      ) {
        search_result {
          edges {
            node {
              ...sr
            }
          }
        }
      }
    }''',
        expected={
            'search': {
                'search_result': {
                    'edges': [
                        {
                            'node': {
                                '__typename': 'SmsFile',
                                'id': 'U21zRmlsZTox',
                                'file_name': 'my_sms_File2.txt',
                                'file_type': 'CPT',
                                'relations': {
                                    'edges': [
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'UNDEFINED',
                                                'thing': {'__typename': 'StrongMotionStation', 'site_code': 'ABCD'},
                                            }
                                        },
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'UNDEFINED',
                                                'thing': {'__typename': 'GeneralTask'},
                                            }
                                        },
                                    ]
                                },
                            }
                        }
                    ]
                }
            }
        },
        query_fragment=search_fragments,
    ),
    SmokeTest(
        query='''query search_general_task {
      search(
        search_term: "agent_name:chrisbc"
      ) {
        search_result {
          edges {
            node {
              ...sr
            }
          }
        }
      }
    }''',
        expected={
            'search': {
                'search_result': {
                    'edges': [
                        {
                            'node': {
                                '__typename': 'GeneralTask',
                                'id': "R2VuZXJhbFRhc2s6Mg==",
                                'created': '2020-10-10T23:00:00+00:00',
                                'updated': None,
                                'title': 'My First Manual task',
                                'description': '##Some notes go here',
                                'agent_name': 'chrisbc',
                                'children': {
                                    'edges': [
                                        {
                                            'node': {
                                                'child': {
                                                    '__typename': 'RuptureGenerationTask',
                                                    'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=',
                                                    'state': 'DONE',
                                                    'result': 'SUCCESS',
                                                    'created': '2020-10-10T23:00:00+00:00',
                                                }
                                            }
                                        }
                                    ]
                                },
                                'files': {
                                    'edges': [
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'READ',
                                                'file': {
                                                    '__typename': 'File',
                                                    'id': 'RmlsZTow',
                                                    'file_name': 'myfile2.txt',
                                                    'file_size': 2000,
                                                },
                                            }
                                        },
                                        {
                                            'node': {
                                                '__typename': 'FileRelation',
                                                'role': 'UNDEFINED',
                                                'file': {
                                                    '__typename': 'SmsFile',
                                                    'id': 'U21zRmlsZTox',
                                                    'file_name': 'my_sms_File2.txt',
                                                    'file_size': 2000,
                                                    'file_type': 'CPT',
                                                },
                                            }
                                        },
                                    ]
                                },
                            }
                        }
                    ]
                }
            }
        },
        query_fragment=search_fragments,
    ),
    SmokeTest(
        query='''query get_file {
      node(id: "RmlsZTow") {
        ... on File {
          file_name
          file_size
          relations {
            edges {
              node {
                ... on FileRelation {
                  role
                  thing {
                    __typename
                    ... on RuptureGenerationTask {
                      created

                    }
                  }
                }
              }
            }
          }
        }
      }
    }''',
        expected={
            'node': {
                'file_name': 'myfile2.txt',
                'file_size': 2000,
                'relations': {
                    'edges': [
                        {
                            'node': {
                                'role': 'WRITE',
                                'thing': {
                                    '__typename': 'RuptureGenerationTask',
                                    'created': '2020-10-10T23:00:00+00:00',
                                },
                            }
                        },
                        {'node': {'role': 'READ', 'thing': {'__typename': 'GeneralTask'}}},
                    ]
                },
            }
        },
    ),
    SmokeTest(
        query='''query get_task {
      node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
          __typename
        ... on RuptureGenerationTask {
          id
          created
          duration
          state
          result

          #rupture_count

          parents {
            edges {
              node {
                parent {
                  ... on GeneralTask {
                    title
                    description
                  }
                }
              }
            }
          }
          files {
            edges {
              node {
                __typename
                ... on FileRelation {
                  role
                  file {
                    ... on File {
                    file_name
                    }
                  }
                }
              }
            }
          }
        }
      }
    }''',
        expected={
            'node': {
                '__typename': 'RuptureGenerationTask',
                'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=',
                'created': '2020-10-10T23:00:00+00:00',
                'duration': None,
                'state': 'DONE',
                'result': 'SUCCESS',
                'parents': {
                    'edges': [
                        {'node': {'parent': {'title': 'My First Manual task', 'description': '##Some notes go here'}}}
                    ]
                },
                'files': {
                    'edges': [
                        {'node': {'__typename': 'FileRelation', 'role': 'WRITE', 'file': {'file_name': 'myfile2.txt'}}}
                    ]
                },
            }
        },
    ),
    SmokeTest(
        query='''query get_node {
      node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=")
      {
        __typename
        ... on RuptureGenerationTask {
          state
          created
          result
          state
        }
      }
    }
    ''',
        expected={
            'node': {
                '__typename': 'RuptureGenerationTask',
                'state': 'DONE',
                'created': '2020-10-10T23:00:00+00:00',
                'result': 'SUCCESS',
            }
        },
    ),
    SmokeTest(
        query='''query search_automation_task {
      search(
        search_term: "task_type:inversion"
      ) {
        search_result {
          edges {
            node {
              ...sr
            }
          }
        }
      }
    }''',
        expected={
            "search": {
                "search_result": {
                    "edges": [
                        {
                            "node": {
                                "__typename": "AutomationTask",
                                "id": "QXV0b21hdGlvblRhc2s6Mw==",
                                "created": "2020-10-10T23:00:00+00:00",
                                "task_type": "INVERSION",
                                "args_at": [{"k": "max_jump_distance", "v": "55.5"}],
                            }
                        }
                    ]
                }
            }
        },
        query_fragment=search_fragments,
    ),
    SmokeTest(
        query='''
      query get_new_task {
        node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjQ=") {
            __typename
          ... on RuptureGenerationTask {
            id
            created
            arguments {k v}
          }
        }
      }''',
        expected={
            "node": {
                "__typename": "RuptureGenerationTask",
                "id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjQ=",
                "created": "2020-10-10T23:00:00+00:00",
                "arguments": [
                    {"k": "max_jump_distance", "v": "55.5"},
                    {"k": "max_sub_section_length", "v": "2"},
                    {"k": "max_cumulative_azimuth", "v": "590"},
                    {"k": "min_sub_sections_per_parent", "v": "2"},
                    {"k": "permutation_strategy", "v": "DOWNDIP"},
                ],
            }
        },
    ),
    SmokeTest(
        query='''mutation new_rupt_file {
        create_file(file_name:"myfile2.txt"
        file_size: 1125899906842624
        md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        meta: [{ k:"encoding" v:"utf8"}]
        ) {
            file_result {
              id
              file_size
              meta {k v}
            }
        }
    }''',
        expected={
            'create_file': {
                'file_result': {
                    'id': 'RmlsZToy',
                    'file_size': 1125899906842624,
                    'meta': [{'k': 'encoding', 'v': 'utf8'}],
                }
            }
        },
    ),
]


def setup(queries):
    # TODO thjis should check there are no errors in response
    headers = {"x-api-key": auth_token}
    transport = RequestsHTTPTransport(url=api_url, headers=headers, use_json=True)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    for q in queries:
        print('setup_query: ', q)
        print()
        response = client.execute(gql(q))
        print(response)
        assert response.get('errors') is None
        print()


if __name__ == "__main__":
    # cleanup environment
    os.system('curl -X DELETE "localhost:9200/toshi_index_mapped?pretty"')
    # assert 0
    os.system('rm -R /tmp/nzshm22-toshi-api-local/*')
    os.system('touch ./graphql_api/api.py')  # force restart of the local WSGI service
    time.sleep(1)

    # create some content with graphql mutations
    setup(test_setup)
    time.sleep(2)
    print("setup complete...")

    # execute some graphql queries
    for test in smoketests:
        time.sleep(0.05)
        test.execute()

    print()
    print("########################")
    print("Smoke tests completed OK")
    print("########################")

    print("##########################################################################################################")
    print("ALERT: Now that we have new node_ids, the sls wsgi server MUST be restarted for each run of this smoketest")
    print("       because tests depend on stable IDs")
    print("       please check that you see this message from server, after the restart")
    print("       `Offline, setting random seed for tests`")
    print("##########################################################################################################")
