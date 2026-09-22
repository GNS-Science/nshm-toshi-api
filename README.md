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

Configuration is managed by environment variables and `.env` files. There is no
central config module; each setting is read with `os.environ.get(...)` in the module
that uses it. The file `.env.example` includes the commonly used development setups.

Deployed values are wired on the `graphql` function in `serverless.yml`:

| Variable | Purpose |
|---|---|
| `ES_ENDPOINT` | Elasticsearch domain URL for search indexing. **Unset means indexing is off** — it does not default to localhost. Not set on the test stage, which has no domain (#377). |
| `ES_INDEX` | Index to write to (`toshi_index_mapped`, the index weka searches). |
| `ES_REGION` | Region used to SigV4-sign requests to the domain. |
| `GRAPHQL_PATH` | Route the GraphQL endpoint is mounted on (`/graphql`). |
| `S3_BUCKET_NAME` | Bucket for file objects and the legacy S3 read fallback. |
| `FIRST_DYNAMO_ID` | Starting ID for new objects (0 for smoketests, 100000 for production). |

Requests to an AWS Elasticsearch domain (`*.es.amazonaws.com`) are signed with the
Lambda's IAM role; a local docker Elasticsearch is not. `graphql_api/tests/test_serverless_config.py`
fails CI if this wiring goes missing from `serverless.yml`.

### Search indexing alarm

Indexing failures never fail a mutation, but each one is logged at ERROR with the
marker `ES_INDEX_FAILURE`. A CloudWatch alarm (`<stack>-es-index-failures`) fires
when that marker appears in an hour and notifies an SNS topic, whose ARN is the
stack output `IndexingAlarmTopicArn`. **The email subscription is not in the
template** — add it by hand in the SNS console after the first deploy of a stage,
and confirm the email AWS sends. Re-subscribe if the stack is ever rebuilt.

## Smoketest

in your `.env` file
```
SLS_OFFLINE=1
TESTING=0
TOSHI_FIX_RANDOM_SEED=1
FIRST_DYNAMO_ID=0 
ES_ENDPOINT=http://localhost:9200
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
then in the simple-toshi-ui repo,
set REACT_APP_GRAPH_ENDPOINT=http://localhost:5000/graphql,
and run yarn start

now if you navigate to http://localhost:3000/Find and find R2VuZXJhbFRhc2s6MjQ4ODdRTkhH
you will get to your test data
