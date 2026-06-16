# ADR-001: GraphQL Schema Evolution Strategy — Legacy Parity, Modern Defaults, Deprecation Aliases

## Status

Proposed.

> **Path note (ADR-004):** What this ADR calls "the POC at
> `spike/strawberry_poc/`" now lives at `graphql_api/`, and the
> parity tool is `graphql_api/tools/schema_parity.py`. The legacy
> Flask/Graphene tree has been removed. References below preserved
> as historical context.

## Context

### The drop-in promise

The Strawberry+FastAPI POC (`spike/strawberry_poc/`) was scoped from
the outset as a **drop-in replacement** for the legacy Graphene+Flask
GraphQL API. Clients — weka, runzi, anything else that reads or
writes via the Toshi GraphQL endpoint — should not need code changes
when traffic moves from `/graphql` to `/graphql-v2`.

That promise is harder than it sounds, because the schemas have
drifted in ways that aren't always visible from a casual read.

### What the parity diff revealed

`spike/strawberry_poc/tools/schema_parity.py` produces an SDL-level
diff between the legacy schema and the POC. The first real run found:

- 30 types in legacy but missing from POC
- 55 types in POC but missing from legacy
- 68 types whose fields, types, or interfaces differ

That is **a lot** of difference for an API that's supposed to be
drop-in.

### The "why does weka work at all?" puzzle

Given that level of divergence, it is genuinely surprising weka
queries succeed at all against `/graphql-v2`. There are several
reasons they do — and understanding them is load-bearing for the
strategy below:

1. **Most divergence is at the SDL level, not the wire level.**
   `[KeyValuePair]` vs `[KeyValuePair!]`, `parents: TaskTaskRelationConnection`
   vs `parents: TaskRelationsConnection!`, edge node nullability — all
   produce identical JSON for the same data. Clients don't notice.

2. **weka uses fragment queries against interfaces.** Most weka query
   bodies look like `... on InversionSolutionInterface { file_name, … }`.
   The interface fragment payload doesn't care about the concrete
   type's name — `File` vs `ToshiFile` is invisible inside a fragment
   that asks for `file_name`. Type-name renames are a much bigger
   problem for `... on ConcreteType { }` fragments than for interface
   fragments. weka mostly uses interfaces.

3. **Production paths that hit the rough edges aren't exercised every
   day.** The two bugs that have actually bitten in this iteration
   (`GeneralTask` enum coercion crashing every field; `file_size`
   silently truncating at 2GB) only surfaced when specific
   real-production data hit specific code paths. Before that, the
   POC "worked" against test data because the test data didn't
   contain the trigger conditions.

4. **GraphQL is permissive about missing data.** When a resolver
   returns `null` for a missing field, the client sees `null` —
   indistinguishable (from the client's perspective) from a value
   that just happens to be `null` legitimately. Silent breakage is
   the default mode of GraphQL schema drift.

5. **The /graphql-v2 deploy has been read-only and narrowly tested.**
   `DB_READ_ONLY=1` blocks every mutation path. The endpoint has
   never been hit at the full breadth of production query patterns;
   the divergences that would bite first under real load haven't had
   a chance to manifest.

So the answer to "why does weka work at all?" is **a combination of
SDL-vs-wire indirection, fragment-based queries that hide type-name
drift, untested code paths, GraphQL's permissive null semantics, and
a read-only deploy**. None of these is a guarantee of correctness —
they're the reasons the divergence has been able to stay invisible.

### The legacy schema is five years old

Many of the conventions in the legacy schema reflect their era:

- Built ~2020 against Graphene 2.x and Graphene-Django defaults.
- Relay 1 was the de facto Relay spec at the time — `clientMutationId`
  was required on every mutation.
- Custom typed scalars (`DateTime`, `JSONString`) were the common
  workaround for Python-side serialisation.
- `auto_camel_case=False` was used to match the Python codebase style.
- Root types named `QueryRoot` / `MutationRoot` — a Graphene
  convention that was never standard but was common in 2018-2020.

By 2026, the GraphQL community has moved on from some of these:

- **Relay 2** dropped `clientMutationId`. Modern Apollo Client / urql /
  Relay 2 clients don't need it.
- **camelCase** is the overwhelming community standard for field
  names. snake_case is valid but uncommon in public APIs.
- **The Relay Connection spec** is normative camelCase for PageInfo
  fields (`hasNextPage`, `endCursor`, etc.). Strawberry follows the
  spec; legacy diverged via its `auto_camel_case=False`.
- **Plain `Query` / `Mutation`** root type names are the convention
  in essentially every public GraphQL API.
- **Typed scalars** like `DateTime` are still good and still common —
  this is one place legacy got it right and the POC regressed (using
  plain `String`).

The legacy schema is not "wrong" — it reflects the standards of its
time, and those standards were defensible. But the gap between
2020 standards and 2026 standards means a clean port has to make
explicit choices.

## Decision

Three principles for how the POC schema relates to the legacy one:

### Principle 1: Wire-format compatibility is the hard contract

**The JSON payload returned for a given query must be identical
between legacy and POC for the same data.**

This is the line that "drop-in replacement" actually means. SDL
differences that don't change the wire format are tolerated; SDL
differences that do change it are bugs.

In practice this means:

- **Field names match.** `pageInfo.hasNextPage` (camelCase) returned
  by legacy must be available as `pageInfo.hasNextPage` from POC,
  even though POC's default scheme is snake_case.
- **Scalar wire format matches.** `created` returned as
  `"2024-01-01T00:00:00Z"` in legacy must be the same string in POC,
  whether the SDL says `String` or `DateTime`.
- **List semantics match.** `[KeyValuePair]` vs `[KeyValuePair!]`
  return the same JSON; tolerated as SDL-only.
- **Required-input mutation fields match.** If legacy accepts
  `clientMutationId: String` in its mutation inputs, POC must too —
  even if the field is ignored downstream.

### Principle 2: Treat the legacy schema as the spec, but selectively modernise where the community has hardened

Where 2020 and 2026 conventions disagree:

- If the **modern community standard has hardened** (Relay spec on
  PageInfo; `Query` / `Mutation` as root names; non-null modifiers
  where appropriate), POC adopts the modern form.
- If the legacy choice is **still acceptable** and switching is
  invisible to clients (snake_case field names; custom scalars), we
  keep the legacy convention.
- If POC has **regressed** vs legacy on a still-good convention
  (typed scalars `DateTime`, `JSONString`), we restore the legacy
  form.

### Principle 3: Backwards compatibility via GraphQL's `@deprecated` directive

Where modern community standard differs from legacy in a
wire-affecting way (PageInfo field naming, `clientMutationId`), expose
**both** names — modern as preferred, legacy as `@deprecated` alias.

Strawberry supports this natively via
`strawberry.field(deprecation_reason="...")`. Multiple fields can point
at the same resolver. Clients can introspect the deprecated marker
and tooling (GraphiQL, Apollo Studio autocomplete) surface it as a
warning, but existing queries keep working.

This pattern is how mature GraphQL APIs (GitHub, Shopify, Stripe)
evolve without breaking clients. After a measurement window (12+
months of query-log evidence), deprecated fields can be removed.

## Specific decisions

| Item | Legacy | Community 2026 | Decision |
|---|---|---|---|
| `PageInfo` field naming | snake_case (`has_next_page`) | **camelCase** (Relay spec normative) | **Both** — camelCase preferred, snake_case deprecated alias |
| `clientMutationId` in mutations | Required (Relay 1) | Dropped (Relay 2) | **Both** — input accepts, output echoes, marked deprecated |
| `DateTime` scalar | Yes | Yes (Strawberry has it) | **Restore in POC** — was wrongly downgraded to `String` |
| `JSONString` scalar | Yes | Yes; `JSON` is alternative | **Restore in POC** — same regression |
| Root type names | `QueryRoot`/`MutationRoot` | `Query`/`Mutation` | **Modernise** — clients don't reference roots by name; zero impact |
| snake_case field names everywhere | snake_case | camelCase preferred | **Keep snake_case** — weka/runzi are Python clients; switching is a separate strategic call |
| Inner nullability `[X]` vs `[X!]` | Permissive nullable | Strict non-null where known | **Modernise** — wire-equivalent, no client impact |
| Connection type naming (e.g. `FileRelationConnection`) | Mixed | No standard | **Align with legacy** for parity — `FileRelationConnection` not the auto-generated POC name |
| `BigInt` scalar | Yes | Common as custom scalar | **Keep** — added to POC for `file_size` >2GB |

## Migration path

### Phase 1 — Wire-breaking fixes (this iteration)

For each item where the SDL difference produces different wire
output:

1. Add the legacy form as a deprecated alias alongside the modern
   form (PageInfo, mutation `clientMutationId`).
2. Restore the typed scalars (`DateTime`, `JSONString`).
3. Pick connection type names that match legacy.

### Phase 2 — Codegen alignment (this iteration)

Wire-format is fine but typed-client codegen breaks:

1. Rename root types to `QueryRoot` / `MutationRoot`.
2. Rename mutation payloads to match legacy (`CreateAutomationTask`
   not `CreateAutomationTaskPayload`).
3. Ensure auto-generated `XxxConnection` / `XxxEdge` types align.

### Phase 3 — Monitor, deprecate, sunset (12+ months out)

1. Add Strawberry resolver instrumentation that logs deprecated-field
   usage to CloudWatch / metrics.
2. Annual review: deprecated fields with zero usage in the past 12
   months can be removed in a major version bump.
3. Communicate sunset timeline to client teams.

## Consequences

### Positive

- The drop-in promise is upheld for existing clients. weka and runzi
  continue working without code changes — even with the bugs that
  were silently bypassing the issue (Principle 1 makes wire format
  the contract, not SDL parity).
- New clients adopting `/graphql-v2` see modern conventions in
  autocomplete and codegen. They don't carry forward 2020-era debt.
- The deprecation pattern gives us a **measured exit path** — we can
  remove legacy fields when we have query-log evidence nobody uses
  them, not based on a guess.
- The schema parity diff tool (`tools/schema_parity.py`) becomes a
  durable CI safety net. Once allowlisted for the intentional
  divergences listed here, every future schema change either fits
  the allowlist or fails the build.

### Negative

- Maintenance cost from carrying deprecated aliases — every `PageInfo`
  field exists twice; every mutation has a `clientMutationId` it
  doesn't actually use. Mitigated by the documented sunset policy
  (Phase 3) but real until then.
- The schema is **slightly more complex** to read — two ways to
  spell the same field. New contributors need to understand which is
  preferred. Mitigated by inline `deprecation_reason` strings.
- **Decision fatigue** — every future schema-affecting change now has
  to consider both forms. We need to make the deprecation pattern
  easy to apply consistently (helper decorators, lint rules) or it
  will rot.

### Neutral

- This ADR doesn't take a position on the **global snake_case vs
  camelCase migration**. That's a separate decision worth its own
  ADR if/when client teams want to undertake it. PageInfo is treated
  as a special case because the Relay spec is normative for it; the
  rest of the schema stays snake_case.
- This ADR doesn't address **schema namespacing for federation** or
  **schema versioning** more broadly. If the API ever moves to
  GraphQL Federation, this ADR's deprecation policy will need to be
  reconciled with the federation supergraph composition rules.

## Lessons captured

The "why does weka work at all?" analysis is the most important part
of this ADR for future maintainers. The five reasons listed there
explain how serious schema drift can hide in plain sight, and they
should be considered every time someone proposes "we don't need to
worry about that divergence":

- "It's just an SDL difference" doesn't mean it's invisible — the
  divergence has been silently producing null fields in production.
- "weka hasn't complained" doesn't mean weka can't hit the broken
  path — it means it hasn't yet.
- "It's read-only and well-tested" applies to the deploys we've made,
  not to the schema. Schema bugs surface when real production traffic
  hits unexpected code paths.

The schema parity diff is the systematic version of this analysis.
We should run it before every cutover-affecting deploy, and we
should resist the urge to allowlist new divergences without first
checking they're truly wire-equivalent or covered by a deprecation
alias.

## Related decisions

- [ADR-002](ADR-002-schema-interface-hierarchy-and-input-naming.md):
  Schema interface hierarchy and input naming conventions — covers
  the remaining divergences after Phase 1+2 (`Thing` /
  `AutomationTaskInterface` adoption, input type naming style,
  auto-generated Edge types).
- (Future) ADR-003: Custom scalar policy — naming, behaviour, and
  on-disk representation conventions for `DateTime`, `JSONString`,
  `BigInt`, and any future scalars (the specific decisions in this
  ADR cover the existing scalars; an ADR is owed when we add the next).
- (Future) ADR-004: Deprecation logging and sunset policy — how we
  measure deprecated-field usage and when we remove (Phase 3 of
  this ADR's migration path).
- (Future) ADR-005: snake_case vs camelCase for client-facing
  fields — strategic call on whether to undertake the broader
  migration.
