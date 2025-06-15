	# nshm-tosh-api
Where NSHM experiments and outputs are captured (not so old fashioned, tosh).

## Getting started

Java is required.

```bash
virtualenv nshm-toshi-api
npm install --save serverless
npm install --save serverless-dynamodb
npm install --save serverless-s3-local
npm install --save serverless-python-requirements
npm install --save serverless-wsgi
sls dynamodb install

poetry install
```

## running `sls` (alias for `serverless` )

NB to run the following examples, depending on local NPM configuration, it may be necessary to run `serverless`, or `npx serverless` instead of `sls`.

You might have to add this block to your AWS credentials file:
```config
[default]
aws_access_key_id=MockAccessKeyId
aws_secret_access_key=MockAccessKeyId
```


## Smoketest
```bash
poetry shell
sls dynamodb start --stage local &\
sls s3 start &\
SLS_OFFLINE=1 TOSHI_FIX_RANDOM_SEED=1 FIRST_DYNAMO_ID=0 sls wsgi serve
```
If `shell` is not available, in `poetry`, it is possible to use `eval $(poetry env activate)`

Then in another shell,
```bash
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
```
(to just run locally stop here)

Then in another shell,
```bash
poetry run python3 graphql_api/tests/smoketests.py
```

## Unit test
```bash
SLS_OFFLINE=1 TESTING=1 poetry run pytest
```

## Test locally with Toshi UI

```
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
sls dynamodb start --stage local &\
sls s3 start &\
SLS_OFFLINE=1 sls wsgi serve
```
then in another shell,
```
SLS_OFFLINE=1 S3_BUCKET_NAME=nzshm22-toshi-api-local S3_TEST_DATA_PATH=s3_extract python3 graphql_api/tests/upload_test_s3_extract.py 
```
then in the simple-toshi-ui repo,
set REACT_APP_GRAPH_ENDPOINT=http://localhost:5000/graphql,
and run yarn start

now if you navigate to http://localhost:3000/Find and find R2VuZXJhbFRhc2s6MjQ4ODdRTkhH
you will get to your test data
