# graphql_api

The GraphQL API for `nshm-toshi-api`: Strawberry + FastAPI, served via
Mangum on AWS Lambda, backed by DynamoDB + S3 + Elasticsearch.

## Where things are

```
graphql_api/
  app.py          FastAPI + Mangum entry point (Lambda handler: app.handler)
  schema.py       Root Strawberry schema — Query + Mutation, AuthExtension wired
  auth.py         AuthExtension: toshi/read + toshi/write scope enforcement
  models/         One file per GraphQL type
  data/           DynamoDB / S3 / Elasticsearch helpers
  tests/          pytest suite (testcontainers-driven)
  tools/          SDL dump, schema-parity diff, runzi corpus refresh
```

## Running

Tests (Docker required for testcontainers):

```bash
uv run pytest
```

Local dev server:

```bash
uv run uvicorn graphql_api.app:app --reload
```

## See also

- `../CLAUDE.md` — architecture overview, conventions, testing patterns
- `../docs/adrs/` — ADRs (schema evolution, interface naming, code reorg)
