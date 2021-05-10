"""
Run all these queries manually in sequence  to validate current behaviour.

Some duplication in existing tests, but not everything.

Setup:
 - docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
 - rm -R /tmp/nshm-toshi-api-local/*
 - sls s3 start &
 - sls wsgi serve

now python3 smoketests.py
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time

import os

api_url = os.getenv('TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
auth_token = os.getenv('TOSHI_API_KEY', "")

class SmokeTest():

  def __init__(self, query, expected, query_fragment = None):
    self.query = query
    self.expected = expected
    self.query_fragment = query_fragment

    headers = {"Authorization": "Bearer %s" % auth_token}
    headers = {"x-api-key": auth_token}
    transport = RequestsHTTPTransport(url=api_url, headers=headers, use_json=True)

    self._client = Client(transport=transport,
            fetch_schema_from_transport=True)

  def execute(self):

    qry = self.query
    if self.query_fragment:
        qry = self.query_fragment + '\n\n' + self.query

    gql_query = gql(qry)
    # print(gql_query)

    self._client.validate(gql_query)

    response = self._client.execute(gql_query)
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
        md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
            file_result {
              id
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
          file_relation{
            id
          }
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
        file_relation{
          id
        }
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
        thing_id:"R2VuZXJhbFRhc2s6Mg=="
        role:READ
      ) {
        ok
        file_relation{
          id
        }
      }
    }''',
    '''mutation new_gt_smsfile_relation {
      create_file_relation(
        file_id: "U21zRmlsZTox"
        thing_id:"R2VuZXJhbFRhc2s6Mg=="
        role:UNDEFINED
      ) {
        ok
        file_relation{
          id
        }
      }
    }''',
    '''mutation new_task_subtask_relation {
      create_task_relation(
        child_id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE="
        parent_id:"R2VuZXJhbFRhc2s6Mg==")
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
      create_grand_inversion_task (input:{
          result:UNDEFINED
          state:UNDEFINED
          created:"2020-10-10T23:00Z"
          arguments: {
              constraints: [
                {constraint_type:MFD_Inequality constraint_weight: 1000}
                {constraint_type:MFD_Equality constraint_weight:10}
                {constraint_type:Slip_Rate constraint_weight: 100} ]
              energy_completion_criteria: {
                energy_delta:0
                energy_percent_delta:10
                look_back_mins:15
              }
              time_completion_criteria:{ minutes:60 }
              sync_interval: 1000
              gutenberg_richter_mfd: {
                total_rate_m5: 5.1
                b_value: 1.0
                mfd_min: 5.0
                mfd_max: 8.5
                mfd_transition_mag: 8.75
                mfd_num: 40
              }
          }
        git_refs: {
          opensha_core: "A"
          opensha_ucerf3:"B"
          opensha_commons:"C"
          nshm_nz_opensha:"D"
        }
        metrics: {
          subsection_count: 3600
          total_energy:3280.2333
        }

      }) {
        task_result {
          id
          created
          arguments {
            energy_completion_criteria {
              energy_delta
            }
          }
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
            git_refs: {
                opensha_ucerf3: "ABC"
                opensha_commons: "ABC"
                opensha_core: "ABC"
                nshm_nz_opensha: "ABC"
            }
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
    ''']

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

  ... on GrandInversionTask {
    id
    created
    arguments {
      energy_completion_criteria {
          energy_delta
          energy_percent_delta
          look_back_mins
      }
    }
  }
}
'''

smoketests = [
  SmokeTest(query = '''query search_sms {
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
    expected = {'search': {'search_result': {'edges': [{'node': {'__typename': 'StrongMotionStation',
      'id': 'U3Ryb25nTW90aW9uU3RhdGlvbjow', 'created': '2020-10-10T23:00:00+00:00', 'site_code': 'ABCD',
      'site_class': 'B', 'site_class_basis': 'SPT', 'liquefiable': None, 'Vs30_mean': [200.0], 'files': {'edges': [
      {'node': {'__typename': 'FileRelation', 'role': 'UNDEFINED', 'file': {'file_name': 'my_sms_File2.txt', 'file_size': 2000}}}]}}}]}}},
    query_fragment = search_fragments),

  SmokeTest(query = '''query search_rupture {
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
    expected = {'search': {'search_result': {'edges': [{'node': {'__typename': 'RuptureGenerationTask',
      'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=', 'result': 'SUCCESS', 'state': 'DONE', 'args': None,
      'files': {'edges': [
      {'node': {'__typename': 'FileRelation', 'role': 'WRITE', 'file': {'id': 'RmlsZTow', 'file_name': 'myfile2.txt', 'file_size': 2000}}}]}}}]}}},
    query_fragment = search_fragments),

  SmokeTest(query = '''query search_file {
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
    expected = {'search': {'search_result': {'edges': [{'node': {'__typename': 'SmsFile',
      'id': 'U21zRmlsZTox', 'file_name': 'my_sms_File2.txt', 'file_type': 'CPT', 'relations': {'edges': [
      {'node': {'__typename': 'FileRelation', 'role': 'UNDEFINED', 'thing': {'__typename': 'StrongMotionStation', 'site_code': 'ABCD'}}},
      {'node': {'__typename': 'FileRelation', 'role': 'UNDEFINED', 'thing': {'__typename': 'GeneralTask'}}}]}}}]}}},
    query_fragment = search_fragments),

  SmokeTest(query = '''query search_general_task {
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
    expected = {'search': {'search_result': {'edges': [{'node': {'__typename': 'GeneralTask',
    'id': 'R2VuZXJhbFRhc2s6Mg==', 'created': '2020-10-10T23:00:00+00:00', 'updated': None, 'title': 'My First Manual task',
    'description': '##Some notes go here', 'agent_name': 'chrisbc',
    'children': {'edges': [
      {'node': {'child': {'__typename': 'RuptureGenerationTask', 'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=', 'state': 'DONE', 'result': 'SUCCESS', 'created': '2020-10-10T23:00:00+00:00'}}}]},
    'files': {'edges': [
      {'node': {'__typename': 'FileRelation', 'role': 'READ', 'file': {'__typename': 'File', 'id': 'RmlsZTow', 'file_name': 'myfile2.txt', 'file_size': 2000}}},
      {'node': {'__typename': 'FileRelation', 'role': 'UNDEFINED', 'file': {'__typename': 'SmsFile', 'id': 'U21zRmlsZTox', 'file_name': 'my_sms_File2.txt', 'file_size': 2000, 'file_type': 'CPT'}}}]}}}]}}},
    query_fragment = search_fragments),

 SmokeTest(query = '''query get_file {
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
    expected = {'node': {'file_name': 'myfile2.txt', 'file_size': 2000,
      'relations': {'edges': [
        {'node': {'role': 'WRITE', 'thing': {'__typename': 'RuptureGenerationTask', 'created': '2020-10-10T23:00:00+00:00'}}},
        {'node': {'role': 'READ', 'thing': {'__typename': 'GeneralTask'}}}]}}}

    ),

 SmokeTest(query = '''query get_task {
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
    expected = {'node': {'__typename': 'RuptureGenerationTask', 'id': 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=', 'created': '2020-10-10T23:00:00+00:00',
      'duration': None, 'state': 'DONE', 'result': 'SUCCESS',
        'parents': {'edges': [
          {'node': {'parent': {'title': 'My First Manual task', 'description': '##Some notes go here'}}}]},
        'files': {'edges': [{'node': {'__typename': 'FileRelation', 'role': 'WRITE', 'file': {'file_name': 'myfile2.txt'}}}]}}}
    ),

 SmokeTest(query = '''query get_node {
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
    expected = {'node': {'__typename': 'RuptureGenerationTask', 'state': 'DONE', 'created': '2020-10-10T23:00:00+00:00', 'result': 'SUCCESS'}}
    ),

  SmokeTest(query = '''query search_grand_inversion_task {
      search(
        search_term: "arguments.energy_completion_criteria.energy_percent_delta:10"
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
    expected = {"search": {
      "search_result": {
        "edges": [
          {
            "node": {
              "__typename": "GrandInversionTask",
              "id": "R3JhbmRJbnZlcnNpb25UYXNrOjM=",
              "created": "2020-10-10T23:00:00+00:00",
              "arguments": {
                "energy_completion_criteria": {
                  "energy_delta": 0.0,
                  "energy_percent_delta": 10.0,
                  "look_back_mins": 15.0
                }
              }
            }
          }
        ]
      }
    }},
    query_fragment = search_fragments),

 SmokeTest(query = '''
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
    expected = { "node": {
          "__typename": "RuptureGenerationTask",
          "id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjQ=",
          "created": "2020-10-10T23:00:00+00:00",
          "arguments": [
            {"k": "max_jump_distance","v": "55.5"},
            {"k": "max_sub_section_length","v": "2"},
            {"k": "max_cumulative_azimuth","v": "590"},
            {"k": "min_sub_sections_per_parent","v": "2"},
            {"k": "permutation_strategy","v": "DOWNDIP"}
          ]
      }
    }
  ),
]


def setup(queries):
    headers = {"x-api-key": auth_token}
    transport = RequestsHTTPTransport(url=api_url, headers=headers, use_json=True)
    client = Client(transport=transport,
            fetch_schema_from_transport=True)
    for q in queries:
        print('setup_query: ', q)
        print()
        client.execute(gql(q))

if __name__ == "__main__":

    #cleanup environment
    os.system('curl -X DELETE "localhost:9200/toshi-index?pretty"')
    os.system('rm -R /tmp/nzshm22-toshi-api-local/*')

    #create some content with graphql mutations
    setup(test_setup)
    time.sleep(0.5)
    print("setup complete...")

    #execute some graphql queries
    for test in smoketests:
        test.execute()

    print()
    print("########################")
    print("Smoke tests completed OK")
    print("########################")
