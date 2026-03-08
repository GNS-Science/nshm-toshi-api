# Dynamic Pydantic-driven Schema: Dumb or Are They?

## What the proposal actually means

The datastore layer is **already generic** — three PynamoDB models handle all types. The bottleneck is the GraphQL schema layer, where each new domain type requires a hand-written Graphene class. The idea: let Pydantic models (which clients already own) drive schema registration automatically.

---

## Pros

**Pydantic as single source of truth:**
- Clients already maintain these models — eliminates the current duplication between client Pydantic models and server Graphene types
- `strawberry-graphql` has first-class `@strawberry.experimental.pydantic.type` support — auto-generates GraphQL types from Pydantic models with almost no boilerplate
- Adding a new domain type drops from ~100 lines of Graphene boilerplate to a Pydantic class + registration call
- REST support via FastAPI is natural with the same models — `FastAPI` + Pydantic gives you OpenAPI docs, validation, and serialization for free

**Architecture alignment:**
- The existing `clazz_name` / `from_json()` dynamic dispatch already encodes the intent — Pydantic models would formalise it
- REST endpoints can share the same datastore layer (`DataManager`) — no duplication of storage logic
- Scientists/power users already think in Pydantic; this meets them where they are

---

## Cons

**Dynamic schema is dangerous for GraphQL/Relay clients:**
- Relay caches the schema and generates typed fragments at build time — a schema that changes at runtime **breaks web clients silently**
- GraphQL introspection is expected to be stable; Apollo Client caches it
- Any "upload a model → schema changes" flow must be a **deploy-time** operation, not a runtime one

**Security surface:**
- Accepting uploaded Python code (even Pydantic models) into a running Lambda is a severe code execution risk
- Even accepting Pydantic model definitions as JSON Schema has injection/DoS risks (recursive models, deeply nested types)
- Would need strict sandboxing, schema size limits, and validation of the model itself before registration

**Relay compatibility gap:**
- Pydantic → Strawberry auto-generates basic types, but Relay requires `Node` interface, `Connection`/`Edge` pagination, and `ClientIDMutation` — none of which Pydantic knows about
- You'd need a wrapper layer that promotes plain Pydantic types to relay-compatible GraphQL types — this is doable but non-trivial

**Dual protocol complexity:**
- REST + GraphQL over the same data with different validation semantics creates subtle divergence over time (e.g. a field that's nullable in REST but non-null in GraphQL)
- Two auth surfaces, two error formats, two versioning concerns

---

## Realistic Architecture Options

**Option A — Strawberry + Pydantic (best fit, deploy-time only)**
```
Pydantic models (client repo)
  → shared package (PyPI / git submodule)
  → strawberry @pydantic.type decorators (server)
  → GraphQL schema rebuilt on deploy
```
No runtime dynamism. Web clients stay stable. One source of truth. Incremental migration from Graphene.

**Option B — Hybrid Flask/Graphene + FastAPI sidecar**
```
/graphql  →  existing Flask/Graphene  (web app clients, Relay)
/api/v1/* →  FastAPI + Pydantic        (scientist/CLI clients, REST)
         →  shared DataManager         (same DynamoDB/S3 backend)
```
Minimal disruption. REST layer is additive. Pydantic models used directly in FastAPI. GraphQL schema unchanged.

**Option C — Full FastAPI + Strawberry (greenfield)**
```
FastAPI app
  /graphql  → Strawberry (Pydantic-native, Relay-compatible)
  /api/v1/* → FastAPI REST routes
  shared    → Pydantic models, DataManager
```
Clean but highest migration cost. Most future-proof.

---

## Recommendation

| Option | Migration Cost | Relay Safety | REST Support | Dynamic Schemas |
|--------|---------------|--------------|--------------|-----------------|
| A (Strawberry deploy-time) | Medium | Safe | No | No (deploy-time only) |
| B (FastAPI sidecar) | Low | Safe | Yes | No |
| C (FastAPI + Strawberry) | High | Safe | Yes | No |
| Runtime upload | Medium | **Unsafe** | Yes | Yes (risky) |

**Avoid runtime schema uploads** — the Relay breakage risk and security surface aren't worth it.

**Start with Option B**: add a FastAPI sidecar sharing `DataManager`. It's low-risk, immediately useful for scientist/CLI clients, and positions you to migrate GraphQL to Strawberry incrementally (Option A → C) later.
