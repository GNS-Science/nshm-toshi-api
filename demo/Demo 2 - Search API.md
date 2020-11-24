
# Search API

```
query searching {
  search(
    #search_term: "state:started&sort=started:desc&size=10&from=0"
    search_term: "CBGS"
  	#search_term: "bedrock_encountered:true"
  	#search_term: "clazz_name:StrongMotionStation&size=200&sort=created:asc"

  	)
    {
    search_result {
      total_count
      pageInfo {
        startCursor
        hasNextPage
        endCursor
      }
      edges {
        node {
          __typename
					... on StrongMotionStation {
            id
            site_code
            bedrock_encountered
            created
          }
          ... on File {
            file_name
            file_size
          }
          ... on RuptureGenerationTask {
            state
            result
            started
            duration
            arguments {
              max_jump_distance
              max_cumulative_azimuth
            }
            files {
              edges {
                node {
                  task_role
                  file {
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
}

```