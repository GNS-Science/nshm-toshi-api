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
query q2 {
  test_outputs: toshs {
    edges {
      task: node {
        id
        name        
      }
    }
  }
}

mutation newTosh {
  createTosh(
    input: {
    toshName: "Bogus3"
    factionId: "1"
    }) 
  {
    tosh {
      name
      id
    }
  }
}

query Q1_cast_to_Tosh {
    node(id: "VG9zaDoxMA==") {
    __typename
    id
    ... on Tosh {
      name
    }
  }
}
```

Next thing: [file upload](https://github.com/lmcgartland/graphene-file-upload)


```
curl http://localhost:5000/graphql \
  -F operations='{"query": "mutation ($file: Upload!) { myUpload(fileIn: $file) { ok }}", "variables": { "file": null }}' \
  -F map='{ "0": ["variables.file"]}' \
  -F 0=@requirements.txt
```