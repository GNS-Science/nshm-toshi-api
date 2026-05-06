	# nshm-tosh-api
Where NSHM experiments and outputs are captured (not so old fashioned, tosh).

## Getting started

Java is required.

 ```nvm current``` wanting node 22
 
 ### ensure yarn 2
 ```
 corepack enable
 yarn set version berry
 yarn --version
 ```
 
 ### upgrade to yarn
 ```
 yarn install
 yarn npm audit
 ```


```
uv sync
uv lock
# use: source .venv/bin/activate
```

Make sure the dynamob plugin for local tests is installed
```
yarn sls dynamodb install
```

## running `sls` (alias for `serverless` )

You might have to add this block to your AWS credentials file:
```config
[default]
aws_access_key_id=MockAccessKeyId
aws_secret_access_key=MockAccessKeyId
```

## System configuration

Configuration is managed by environment variables and `.env` files.

 - Please see `graphql_api\config.py` for all config options
 - the file `.env.example` includes the commonly used develepment setups  

## Smoketest

in your `.env` file
```
SLS_OFFLINE=1
TESTING=0
TOSHI_FIX_RANDOM_SEED=1
FIRST_DYNAMO_ID=0 
```
then 

```bash
yarn sls dynamodb start --stage local &\
yarn sls s3 start &\

### The serverless wsgi command requires the correct python env, provided via uv
uv run yarn sls wsgi serve
```

If needed, activate the venv directly: `source .venv/bin/activate`

Then in another shell,
```bash
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.1.0
```
(to just run locally stop here)

Then in another shell,
```bash
uv run python3 graphql_api/tests/smoketests.py
```

## Unit test

in your `.env` file
```
SLS_OFFLINE=1
TESTING=1 
```

then

```bash
uv run pytest
```

## Auditing requirements packages

```
uv export --format requirements-txt --no-emit-project --output-file audit.txt
uv run pip-audit -r audit.txt -s pypi --require-hashes
uv run pip-audit -r audit.txt -s osv --require-hashes
```

## Test locally with Toshi UI

```
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.8.0
yarn sls dynamodb start --stage local &\
yarn sls s3 start &\
SLS_OFFLINE=1 uv run yarn sls wsgi serve
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
