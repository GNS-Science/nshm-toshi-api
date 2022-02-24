# nshm-tosh-api
Where all out tests and outputs are buried  - like so much old fashioned, tedious tosh.


## Getting started

```
virtualenv solvis-api
npm install --save serverless
npm install --save serverless-dynamodb-local
npm install --save serverless-s3-local
npm install --save serverless-python-requirements
npm install --save serverless-wsgi
sls dynamodb install
```

## Smoketest
```

sls dynamodb start --stage local & sls s3 start & SLS_OFFLINE=1 TOSHI_FIX_RANDOM_SEED=1 sls wsgi serve
```
Then in another shell,
```
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0,
```
(to just run locally stop here)

Then in another shell,
```
python3 graphql_api/tests/smoketests.py
```

## Unit test
```
TESTING=1 pytest
```
