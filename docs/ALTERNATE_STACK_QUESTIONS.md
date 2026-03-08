# Alternate Stack: Python/Flask/Graphene → Node/Express/Apollo (TSX)

## Context for this project
- AWS Lambda + DynamoDB + S3 + Elasticsearch
- GraphQL schema with ~20+ domain types
- Moto-based test suite
- Serverless Framework deployment

---

## Pros

**TypeScript/Apollo advantages:**
- **Apollo Server** is first-class GraphQL — better tooling, codegen, federation support
- **TypeScript** catches schema/resolver type mismatches at compile time; Graphene's Python typing is weaker
- **Cold start** — Node.js Lambdas typically cold-start faster than Python (no `graphene`/`boto3` import chain)
- **Ecosystem** — `@aws-sdk/v3` is tree-shakeable, reducing bundle size; `esbuild`/`tsx` Lambda bundling is mature
- **Code generation** — `graphql-codegen` can generate TypeScript types from schema, keeping resolvers in sync
- **Relay compatibility** — Apollo + `graphql-relay-js` maps cleanly to your existing relay Node IDs
- **Serverless Framework** support for Node/TS is more actively maintained

**Operational:**
- Node 22 is already your Serverless runtime target (you have `yarn` berry)
- Removes the `poetry run yarn sls wsgi serve` awkwardness (Python wrapped in Node toolchain)

---

## Cons

**Migration cost (high):**
- ~20+ schema types, each with Query + Mutation resolvers — all need rewriting
- `PynamoDB` models → `DynamoDB DocumentClient` (or `dynamoose`) — non-trivial
- `moto` mock suite → `aws-sdk-mock` / `jest` with `@aws-sdk/lib-dynamodb` mocking — full test rewrite
- Elasticsearch client (`elasticsearch-py`) → `@elastic/elasticsearch` — API differs
- `from_json()` dynamic dispatch pattern needs reimplementing (TypeScript is structural, not `getattr`-based)

**Schema fidelity risk:**
- Graphene enforces Python-side types tightly; Apollo resolvers are looser by default — easy to introduce subtle schema regressions
- Relay cursor pagination helpers exist in both but behave slightly differently

**Operational:**
- `moto` is uniquely powerful for AWS mocking — Jest-based AWS mocking is more manual
- If you use DynamoDB Local + S3 local, the Node SDK setup differs slightly

**Team context:**
- If the team is Python-native, ongoing maintenance cost increases
- This is a largely internal data store API — the UX benefits of Apollo (subscriptions, federation) may not apply

---

## Summary

| Factor | Weight |
|--------|--------|
| Schema size (~20 types, full CRUD) | High rewrite cost |
| Team is Python-native | Ongoing cost |
| Lambda cold start matters | Minor benefit |
| Better GraphQL tooling (codegen) | Real but marginal for internal API |
| Removes `wsgi` awkwardness | Small win |

**Recommendation:** Not worth it for this project as-is. The rewrite cost is large, the operational wins are marginal for an internal science data store, and the team context favors Python.

**Better alternative:** If the motivation is DX/typing, consider `strawberry-graphql` as a drop-in Graphene replacement — it has full Python type annotation support, better IDE integration, and the same Serverless/DynamoDB stack.
