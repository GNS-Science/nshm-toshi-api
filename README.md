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

Settings come from environment variables (see `.env.example` for local dev).
Deployed values are set on the `graphql` function in `serverless.yml`:

| Variable | Purpose |
|---|---|
| `ES_ENDPOINT` | Elasticsearch URL. Unset = no search indexing (the case on test). |
| `ES_INDEX` | Index name (`toshi_index_mapped`). |
| `ES_REGION` | AWS region for signing Elasticsearch requests. |
| `GRAPHQL_PATH` | GraphQL route (`/graphql`). |
| `S3_BUCKET_NAME` | S3 bucket for files. |
| `FIRST_DYNAMO_ID` | First ID for new objects (0 for smoketests, 100000 for prod). |

### Search indexing alarm

Failed index writes log `ES_INDEX_FAILURE` and trigger a CloudWatch alarm, which
emails via the SNS topic in stack output `IndexingAlarmTopicArn`. Add the email
subscription by hand in the SNS console after a stage's first deploy.

### Backfilling the search index

`scripts/backfill_search_index.py` re-indexes objects from DynamoDB and legacy S3.
It is a dry run unless `--execute` is given, and safe to re-run. Narrow it with
`--source`, `--store`, `--clazz`, `--since` or `--min-id`; `--index-counts` compares
the index against the stores. Classes in `search.NOT_INDEXED` are always skipped.

The index needs `ignore_malformed` on the `id` field, or objects with suffixed
legacy ids (`10001HzGWM`) are rejected — `id` is mapped as a long, and weka reads
it from `_source` to build result links, so it cannot simply be dropped. It is set
on the live prod index; **a rebuilt index needs it again**:

```
PUT toshi_index_mapped/_mapping  {"properties": {"id": {"type": "long", "ignore_malformed": true}}}
```

The script refuses to write if it is missing.

```bash
uv run python scripts/backfill_search_index.py --stage prod                    # counts only
uv run python scripts/backfill_search_index.py --stage prod --index-counts --endpoint https://<domain-endpoint>
uv run python scripts/backfill_search_index.py --stage prod --execute --endpoint https://<domain-endpoint>
```

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
