# nshm-tosh-api
Where all out tests and outputs are buried  - like so much old fashioned, tedious tosh.


# serverless setup

following guidance here:

https://www.serverless.com/blog/flask-python-rest-api-serverless-lambda-dynamodb/

```
sudo npm install -g serverless

```

## OPTION A openapi-generator


pre-requisites: 
 - nodejs
 - npm (the node package manager

`npx @openapitools/openapi-generator-cli generate -i swagger.yaml -g python-flask -o openapi`


## OPTION B flask-restful

ref https://flask-restful.readthedocs.io/en/latest/quickstart.html


## OPTION C graphql 

example graphql:

```
#record a new task
mutation m1 {
  createTaskResult(
    input: {
      started: "2020-10-30T09:14Z"
      duration: 600
      ruptureGeneratorArgs: {
        maxJumpDistance:55.5
        maxSubSectionLength: 2
        maxCumulativeAzimuth:590
      }
    }) {
     taskResult {
      started
    }
  } 
}

# query tasks
query q1 {
  ruptureGeneratorResults {
    edges {
      node {
        id
        started
        ruptureGeneratorArgs {
          maxJumpDistance
        }
      }
    }
  }
}

## create task-file connection
## NB file upload not available in igraphql client
mutation m2 {
  createTaskFile(
  	fileId:"RGF0YUZpbGU6MA=="
  	taskId:"T3BlbnNoYVJ1cHR1cmVHZW5SZXN1bHQ6MA==") 
  {ok} 
}


```

Next thing: [file upload](https://github.com/lmcgartland/graphene-file-upload)


```
curl http://localhost:5000/graphql \
  -F operations='{"query": "mutation ($file: Upload!) { myUpload(fileIn: $file) { ok }}", "variables": { "file": null }}' \
  -F map='{ "0": ["variables.file"]}' \
  -F 0=@requirements.txt
```
