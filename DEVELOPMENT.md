# Development

Pre-requisites on your development machine:

 - Python3
 - virtualenv
 - NodeJS & the serverless framework, 
   https://www.serverless.com/framework/docs/providers/aws/guide/quick-start
 
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
pytest
```

# Running the service locally

this is the quickest way to try out new features etc as there's no packing/deployment overhead.

 - start a local test S3 instance (data is written to /tmp/nshm-toshi-api-local)
 - start the API running on http://127.0.0.1:5000/graphql
   
```
sls s3 start&
sls wsgi serve
```

Now start interacting with the service with your web browser.

**Notes:**

 - the sls wsgi serve will hot-restart if you change the python
 - you can safely delete contents form nshm-toshi-api-local to see the effects, clean up etc
 


