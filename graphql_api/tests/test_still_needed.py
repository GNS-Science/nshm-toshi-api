"""
Run all these queries manually in sequence  to validate current behaviour.

Some duplication in existing tests, but not everything.

Setup:
 - docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
 - rm -R /tmp/nshm-toshi-api-local/*
 - sls s3 start &
 - sls wsgi serve

then run from http://127.0.0.1:5000/graphql the following
"""
test_needed = '''
mutation new_sms {
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
}

mutation new_ruptgen_task {
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
}

# mutation m1b {
#   update_rupture_generation_task(input: {

#   }) {
#     clientMutationId
#   }
# }

mutation new_rupt_file {
  create_file(file_name:"myfile2.txt"
  file_size: 2000
  md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
      file_result {
        id
      }
  }
}


mutation new_rupt_file_relation {
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
}

mutation new_sms_file {
  create_sms_file(file_name:"my_sms_File2.txt"
  file_size: 2000
  file_type: CPT
  md5_digest: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
      file_result {
        id
        file_type
      }
  }
}

mutation new_sms_file_relation {
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
}


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
                metrics {
                   rupture_count
                }
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
    files {
     edges {
        node {
          __typename
          ... on FileRelation {
            role
            file {
              ... on File {
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
                file_type
              }
            }
          }
        }
      }
    }
  }
}

query search_sms {
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
}

query search_rupture {
  search(
    search_term: "result:UNDEFINED"
    #search_term: "file_name: myfile*"
  ) {
    search_result {
      edges {
        node {
          ...sr
        }
      }
    }
  }
}

query search_file {
  search(
    search_term: "file_name: my_sms*"
  ) {
    search_result {
      edges {
        node {
          ...sr
        }
      }
    }
  }
}


query get_file {
  node(id: "RmlsZTow") {
    ... on File {
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
                    metrics {
                       rupture_count
                    }
                  }
                }
              }
            }
          }
        }
    }
  }
}

query get_task {
  node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjE=") {
    ... on RuptureGenerationTask {
      id
      created
      duration

      metrics {
        rupture_count
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
}

'''
