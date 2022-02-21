# Development

Pre-requisites on your development machine:

 - Python3
 - virtualenv
 - NodeJS & the serverless framework, 
   https://www.serverless.com/framework/docs/providers/aws/guide/quick-start
 - docker for the local ElasticSearch
 
And for actual AWS use 
 - an S3 'free tier' account
 - an S3 role ready for SLS deployment, 
   https://www.serverless.com/framework/docs/providers/aws/guide/credentials/
 
for new developers getting started...
## 1. Clone repo, create & activate the python3 virtualenv

```
git clone git@github.com:GNS-Science/nshm-toshi-api.git
virtualenv -p python3 nshm-toshi-api
cd nshm-toshi-api/
source bin/activate
```

## 2. Setup serverless using NPM

In the project root folder, run `npm install`.

This installs the serverless plugin devDependencies defined in `package.json`.

## 3. Setup the python dependencies with pip

```
pip install -r requirements.txt
pip install -r test_requirements.txt
```

and validate our tests are passing:
```
SLS_OFFLINE=1 pytest
```

## 4. setup docker for elasticsearch

Version 6.8 is ther latest available in AWS.

```
docker pull docker.elastic.co/elasticsearch/elasticsearch:6.8.0
```

# Running the service locally

this is the quickest way to try out new features etc as there's no packing/deployment overhead.

 - start a local test S3 instance (data is written to /tmp/nshm-toshi-api-local)
 - start the API running on http://127.0.0.1:5000/graphql
   
```
sls s3 start&
sls wsgi serve
```
and (perhaps in another shell):

```
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
```

Now start interacting with the service with your web browser.

**Notes:**

 - the sls wsgi serve will hot-restart if you change the python
 - you can safely delete contents form nshm-toshi-api-local to see the effects, clean up etc
 

## basic proof ...

Create a new strong motion station, then find it again. This uses

 - the graphql API
 - the local S3 store 
 - the local docker ES
 
Point your browser at http://127.0.0.1:5000/graphql to see the GraphiQL interface. Now paste these queries into the left-most pane and run them in order.

```
mutation m0 {
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

query searching {
  search(
    #search_term: "site_class_basis:SPT&size=20&sort=created:asc"
    search_term: "ABCD"
  ) {
    search_result {
      edges {
        node {
          ... on StrongMotionStation {
            created
            site_code
            site_class
            site_class_basis
            liquefiable
            Vs30_mean
          }
        }
      }
    }
  }
}
```




