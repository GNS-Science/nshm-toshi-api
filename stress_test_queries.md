
## Stress test queries

```
query q0 {
  #node(id: "R2VuZXJhbFRhc2s6Nw==") {#TEST
  #node(id:"R2VuZXJhbFRhc2s6OQ==") {#LOCAL ...
  #node(id: "R2VuZXJhbFRhc2s6MTI=") {#2 kids OK
  #node(id: "R2VuZXJhbFRhc2s6MjQ=") { #10 kids OK 0.666 delay
  #node(id: "R2VuZXJhbFRhc2s6MzU=") { #10 kids BAD 0.006 delay 
  #node(id: "R2VuZXJhbFRhc2s6NDU=") { #10 kids BAD 0.006 delay
  #node(id: "R2VuZXJhbFRhc2s6Mjk2") { #10o kids BAD 0.002 delay
  #node(id:"R2VuZXJhbFRhc2s6Mzk3") { # 100 GOOD
  #node(id: "R2VuZXJhbFRhc2s6NDk4" ) { # 100 86!!
  #node(id: "R2VuZXJhbFRhc2s6NTk5" ) { # 100 93 !!   
  #node(id: "R2VuZXJhbFRhc2s6NzAw" ) { # 100 93 !!  
  #node(id: "R2VuZXJhbFRhc2s6ODAx" ) { # 100 85 !!
  #node(id: "R2VuZXJhbFRhc2s6OTAy" ) { # 100 91 !! 
  #node(id: "R2VuZXJhbFRhc2s6MTIwNQ==") { #100 99
  #node(id: "R2VuZXJhbFRhc2s6MTUyOQ==") { #100 after trans OK
  #node(id: "R2VuZXJhbFRhc2s6MTYzMA==") { #100 after trans OK
  #node(id: "R2VuZXJhbFRhc2s6MTczMQ==") { #100 after trans OK
  #node(id: "R2VuZXJhbFRhc2s6MTgzMg==") { #100 after trans OK 
  #node(id: "R2VuZXJhbFRhc2s6MTkzMw==") { #100 after trans OK     
  node(id: "R2VuZXJhbFRhc2s6Mg==") {
    __typename
    ... on GeneralTask {
      
      title
      created
      children {
        total_count
        edges {
          node {
            child_id
            child {
              __typename
              ... on RuptureGenerationTask {
                id
                state
                result
                created                
                parents {
                  total_count
                  edges {
                    node {
                      parent {
                        id
                      }

                    }
                  }
                }
              }
              ... on AutomationTask {
                id
                files {total_count}
								inversion_solution {
                  file_name
                  id     
                  tables {
                    table_id
                    label
                    table_type
                    created
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


## searching

```
fragment sr on SearchResult {
  __typename
  
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
  }
}

query search_general_task {
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
    }
```  

```
query q30 {
  node(id: "QXV0b21hdGlvblRhc2s6MTA3Mjg=") { #10728
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3MzA=") { #10730
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3NDI=") { #10742 Yes
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3NDM=") { #10743 404
    id
    ... on AutomationTask {
      parents {
        total_count
        edges {
          node {
            parent {
              id
            }
          }
        }
      }
    }
  }
}

query rupt {
  node(id:"RmlsZToy") {
    id
    ... on File {
      meta {k v}
    }
    
  }
}


query qrupts{
  node(id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjg=") { #10728
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3MzA=") { #10730
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3NDI=") { #10742 Yes
  #node(id: "QXV0b21hdGlvblRhc2s6MTA3NDM=") { #10743 404
    id
    ... on RuptureGenerationTask {
      parents {
        total_count
        edges {
          node {
            parent {
              id
            }
            
          }
        }
      }
      
      files {
        total_count
        edges {
          node {
            file {
            __typename
              ... on File {
                id
              }
              ... on FileInterface {
                
                file_name
              }
            }
          }
        }
      }
    }
  }
}
```