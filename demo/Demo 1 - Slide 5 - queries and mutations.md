# Demo 1 - Slide 4

## Queries and Mutations

### Tasks query

```
query {
  ruptureGenerationTasks {
    edges {
      node {
        id
      }
    }
  }
}

```
In our freshly deployed service we should have 0 tasks


### Add a new task 

```
mutation {
  createRuptureGenerationTask(
    input: {
      started: "2020-11-02T09:15Z"
      duration: 600
      ruptureGeneratorArgs: {
        maxJumpDistance:55.5
        maxSubSectionLength: 2
        maxCumulativeAzimuth:590
      }
    }) {   
     taskResult {id}
  } 
}
```
TODO explain how the auth architecture works

 - separate **nshm-toshi-auth** github project to make this re-useable
 - 


 ### re-visit our query

 ```
query {
  ruptureGenerationTasks {
    edges {
      node {
        id
        started
        duration
        ruptureGeneratorArgs {
          maxJumpDistance
          maxCumulativeAzimuth
        }
      }
    }
  }
}

```
showing also
 - field autocompletion
 - query vs result - defining the payload
 - schema documentatation
 - error handling (date format, timezone)