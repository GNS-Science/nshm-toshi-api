# ADR-002: Schema Interface Hierarchy and Input Naming Conventions

## Status

Accepted. Implemented in PR #308 (interface adoption) and PR #309
(additional client-divergence fixes surfaced by the post-implementation
audit; see "Post-implementation audit" below).

## Context

ADR-001 Phase 1+2 closed the wire-breaking and codegen-breaking
divergences between the legacy Graphene schema and the Strawberry
POC. The schema parity diff (`tools/schema_parity.py`) dropped from
657 lines / 257 field mismatches at the spike baseline to ~280 field
mismatches after Phase 1+2. The remaining divergences cluster into
four distinct categories:

| Category | Examples | Wire-impacting? |
|---|---|---|
| 1. Missing interfaces | `Thing`, `AutomationTaskInterface` | **Yes** — fragment queries break |
| 2. Input type naming | `AutomationTaskInput` (legacy) vs `CreateAutomationTaskInput` (POC) | No — codegen only |
| 3. Auto-generated Edge types | `GeneralTaskEdge`, `RuptureSetEdge`, etc. one per node | No — wire-equivalent |
| 4. Custom Connection types | `FileRelationsConnection` (POC) vs `FileRelationConnection` (legacy) | No — already decided in ADR-001 |

Each category needs its own decision: fix, alias, accept as
divergence, or document for a separate ADR. ADR-001's principles
(wire compat is the contract; modernise where standard has hardened;
use `@deprecated` to bridge) apply directly to (1) and (2), and
inform the accept/defer calls for (3) and (4).

### The four categories in detail

**1. Missing interfaces** — Legacy declares `Thing` and
`AutomationTaskInterface` and has concrete types implement them.
At drafting time we assumed both were wire-impacting. A subsequent
client audit (see "Post-implementation audit" below) refined the
picture:

- `AutomationTaskInterface` is **heavily used by weka**:
  `views/GeneralTask/InversionSolutionDiagnosticContainer.tsx`,
  `views/GeneralTask/tabs/GeneralTaskChildrenTab.tsx`,
  `views/AutomationTask/AutomationTaskPage.tsx`,
  `views/Favourites/Favourites.tsx`, plus generated Relay codegen
  files for each. Pattern:
  ```graphql
  ... on AutomationTaskInterface { state result task_type
    arguments { k v }
    parents { edges { node { parent { ... on GeneralTask { id title } } } } }
  }
  ```
  Without the interface, these queries fail GraphQL validation.
  **Real wire-level break.**

- `Thing` is **not used by any inspected client** (weka, nzshm-runzi,
  nzshm-model). Clients reach for concrete fragments instead
  (`... on GeneralTask`, `... on AutomationTask`). Adopting `Thing`
  in the POC remains defensive SDL-parity work rather than a
  load-bearing fix — useful for future-proofing and for the parity
  diff signal-to-noise, but no observed client query depends on it.

POC has neither. The concrete types (`GeneralTask`, `AutomationTask`,
etc.) already declare equivalent fields directly — the structural
information is there, just not the interface declaration that lets
fragment queries resolve.

**2. Input type naming** — Legacy uses
`<TypeName>Input` (for create) and `<TypeName>UpdateInput` (for update):

```
AutomationTaskInput          (legacy create input)
AutomationTaskUpdateInput    (legacy update input)
```

POC uses Strawberry's modern convention:

```
CreateAutomationTaskInput
UpdateAutomationTaskInput
```

Both work. Wire JSON is identical (`{ "input": { ... } }`). The
difference shows up only in typed-client codegen: sgqlc emits one
file per input type, and the file name changes.

**3. Auto-generated Edge types** — Strawberry's relay layer emits
one `XxxEdge` type per concrete node type:

```
GeneralTaskEdge
RuptureSetEdge
ToshiFileEdge
... and so on for every node type
```

Legacy used a smaller set of shared connection/edge types:

```
FileEdge        (used by every File-typed connection)
ThingEdge       (used by every Thing-typed connection)
```

Wire JSON is identical — clients see `{ edges: [{ node: {...} }] }`
either way. The SDL difference is purely structural and affects only
codegen tooling that generates one wrapper class per Edge type.

**4. Custom Connection naming** — already decided in ADR-001
(`FileRelationsConnection` vs legacy `FileRelationConnection`,
`TaskRelationsConnection` vs `TaskTaskRelationConnection`). ADR-001's
position: accept the small POC-side rename rather than fight
Strawberry's auto-generation collision. Re-flagged here only to
explain why these names appear in the diff without further action.

## Decision

### Principle (carried forward from ADR-001)

Wire compat is the contract. SDL differences that don't change the
JSON over the wire are tolerated; SDL differences that change runtime
behaviour are fixed.

### Per-category decisions

#### Category 1 — Missing interfaces: **Adopt both**

Both `Thing` and `AutomationTaskInterface` get added to the POC.
`AutomationTaskInterface` is wire-impacting and confirmed
load-bearing for weka; `Thing` is defensive parity (no observed
client query, but cheap to add alongside and keeps the parity diff
clean). The work is well-scoped because the concrete types already
declare equivalent fields.

#### Category 2 — Input type naming: **Accept the divergence**

Keep the modern Strawberry-style `CreateXxxInput` /
`UpdateXxxInput` naming. Wire format is identical; only codegen
breaks. The ADR-001 principle "modernise where the community has
hardened" applies: the `Create/Update`-prefixed convention is the
norm in 2026 Strawberry / Apollo / Nexus schemas.

Clients regenerating typed code against `/graphql-v2` will see
different file names. This is documented behaviour, not a bug.

#### Category 3 — Auto-generated Edge types: **Accept the divergence**

Strawberry's relay layer generates one Edge per node type. Trying
to consolidate them into shared `ThingEdge`/`FileEdge` types
would require building a custom relay layer — non-trivial work
for codegen-only parity. Wire is identical.

#### Category 4 — Custom Connection naming: **Already resolved**

Per ADR-001. No new action.

## Specific decisions

| Item | Legacy | POC | Decision |
|---|---|---|---|
| `Thing` interface | Declared, implemented by 7 concrete types | Missing | **Adopt** — declare in POC, attach to each concrete type |
| `AutomationTaskInterface` | Declared, implemented by 3 concrete types | Missing | **Adopt** — same pattern |
| Input naming `<Type>Input` | snake-Graphene convention | `Create<Type>Input` (Strawberry-modern) | **Accept divergence** — wire-equivalent, modern preferred |
| Edge types per node | Shared `FileEdge` / `ThingEdge` etc. | Per-type `<Node>Edge` | **Accept divergence** — wire-equivalent, structural cost too high |
| `FileRelationsConnection` etc. | `FileRelationConnection` | Already POC-named | **Already resolved** (ADR-001) |

## Implementation plan for the interface adoptions

### `Thing` interface

**Fields (per legacy SDL):**

```graphql
interface Thing {
  created: DateTime
  files(before: String, after: String, first: Int, last: Int): FileRelationsConnection
  parents(before: String, after: String, first: Int, last: Int): TaskRelationsConnection
  children(before: String, after: String, first: Int, last: Int): TaskRelationsConnection
}
```

(Connection field types use the POC-side naming
`FileRelationsConnection` / `TaskRelationsConnection`, since
ADR-001 ratified those. Clients querying via `... on Thing { ... }`
don't reference the connection type name in their query — they
spell `files { edges { ... } }`.)

**Concrete types that implement `Thing` in legacy:**

- `GeneralTask`
- `AutomationTask`
- `RuptureGenerationTask`
- `OpenquakeHazardTask`
- `OpenquakeHazardSolution`
- `OpenquakeHazardConfig`
- `StrongMotionStation`

Each currently declares the four fields independently in the POC.
Implementation:

```python
# models/thing.py (new)
@strawberry.interface
class Thing:
    created: DateTime | None = None
    # connection fields declared via @relay.connection on each
    # concrete type — interface itself doesn't auto-resolve them
```

For Strawberry to surface `... on Thing { files { ... } }` queries,
the interface must declare the field signatures matching the concrete
types. Implementation will likely follow the same pattern as
`InversionSolutionInterface` (added earlier in this iteration):
declare field signatures on the interface, concrete types resolve.

The pattern was non-trivial when we added `InversionSolutionInterface`
— specifically the relay connection field collisions and the duplicate
edge type generation. Same gotchas apply here. Estimated work: ~1 day
of careful Strawberry plumbing + tests.

### `AutomationTaskInterface`

**Fields (per legacy SDL):**

```graphql
interface AutomationTaskInterface {
  result: EventResult
  state: EventState
  created: DateTime
  duration: Float
  general_task_id: ID
  task_type: TaskSubType
  parents(...): TaskRelationsConnection
  arguments: [KeyValuePair]
  environment: [KeyValuePair]
  metrics: [KeyValuePair]
}
```

**Concrete types:**
- `AutomationTask`
- `RuptureGenerationTask`
- `OpenquakeHazardTask`

Same implementation pattern. Smaller scope because only 3 concrete
types vs 7 for `Thing`.

### Test plan

Per interface:

- Schema-level: `schema.as_str()` contains the `interface <Name>` block.
- Introspection: `__type(name: "Thing")` returns the interface kind.
- Fragment-resolution: `... on Thing { children { ... } }` against a
  concrete `GeneralTask` resolves the children field correctly.
- `nodes(id_in: [...]) { ... on AutomationTaskInterface { parents { ... } } }`
  weka-style traversal works end-to-end.
- Parity diff: `Thing` and `AutomationTaskInterface` disappear from
  the "types only in legacy" list; the "interfaces only in legacy"
  field mismatches for each concrete type also clear.

### Phasing

Both interfaces can land in a single PR (interface declaration +
attach to concrete types + tests). Estimated ~150-300 lines plus
tests.

## Consequences

### Positive

- weka's `... on Thing { ... }` and `... on AutomationTaskInterface { ... }`
  fragment queries work against `/graphql-v2`. This is the single
  largest remaining wire-breaking divergence after Phase 1+2.
- Parity diff drops further — these two interfaces and the field
  mismatches they cause across 7+3 concrete types are all closed
  with one set of changes.
- The legacy `test_nodes_bugfix_220` weka pattern (deep traversal via
  `AutomationTaskInterface.parents`) becomes reproducible against the
  POC, completing the work hinted at in COVERAGE_GAPS.md gap 3.

### Negative

- The interface declarations must declare their connection fields
  with matching arg signatures and types. Strawberry's relay layer
  has known sharp edges when interfaces declare relay connections
  (we hit some of these adding `InversionSolutionInterface`). Risk
  of additional plumbing surfacing during implementation.
- Each concrete type gains an `implements Thing` (and possibly
  `implements AutomationTaskInterface`) declaration. That's
  mechanical but touches 7 files.
- Auto-generated Edge type count stays high (Strawberry per-node).
  Documented divergence; no fix.

### Neutral

- The input naming and Edge type categories are explicitly accepted.
  This is the ADR doing its job — naming a divergence as known and
  intentional rather than letting it generate continuous review
  noise.

## Why the Edge / Input divergences are NOT worth fighting

It's tempting to also align Edge types and input names for full
"drop-in cosmetic parity". Why we don't:

- **Cost**: each requires either a custom Strawberry layer
  (Edge consolidation) or systematic Python-class renames + name=
  decorators on every Input class (input renaming). Tens to hundreds
  of lines plus testing, plus ongoing maintenance overhead.
- **Benefit**: zero wire-format change. The only beneficiaries are
  client codegen pipelines that were already breaking on the
  Graphene→Strawberry transition for *other* reasons (custom scalar
  changes, root type names, etc.).
- **Risk**: maintainability — adding renames just to match legacy
  inconsistencies (recall ADR-001's payload-naming surprise where
  legacy mixed `Create*Payload` and `Create*` based on author whim)
  imports legacy debt into POC.

The cleaner stance is to document these as accepted divergences in
this ADR and let consumers of the SDL know they're intentional.

## Lessons captured (companion to ADR-001's)

Two patterns from the Phase 1+2 implementation work that are worth
preserving for future schema work:

1. **Don't generalise from one type to the whole schema.** Phase 2's
   payload rename script initially assumed "remove the Payload suffix
   from all `Create*Payload` types" — turned out legacy was internally
   inconsistent. The correct fix needed a per-type mapping derived
   directly from the legacy SDL. Schema parity is full of legacy
   inconsistencies; the only safe pattern is to map type-by-type.

2. **Wire-equivalence is not SDL-equivalence.** Many of the most-noisy
   divergences (`[X]` vs `[X!]`, `pageInfo` vs `page_info`, edge
   nullability) produce identical JSON on the wire for the same data.
   The schema parity tool surfaces all SDL differences; deciding
   which are actually wire-breaking requires human judgement. This
   ADR's Category 1 (interfaces) vs Categories 2-4 (SDL cosmetics)
   illustrates the distinction.

## Post-implementation audit (client divergence)

After PR #308 landed the interface adoption, we audited real
production GraphQL queries across three clients to verify the
remaining "POC-only types" in the parity diff were genuinely
acceptable:

- `weka` (UI) — `../UI/weka/src/`
- `nzshm-runzi` (Python automation) — `../MISC/nzshm-runzi`
- `nzshm-model` (Python library) — `../LIB/nzshm-model`

The audit confirmed Categories 2–4 are safe to accept, but surfaced
**four additional wire-breaking divergences** that ADR-002's original
analysis missed. All four are fixed in PR #309.

| # | Divergence | Client evidence | Fix |
|---|---|---|---|
| A | POC SDL type `ToshiFile` (POC-only rename of legacy `File`) | weka × 4 source files (`... on File`), nzshm-model × 1 | Revert SDL name to `File`; keep Python class as `ToshiFile` via `@strawberry.type(name="File")` |
| B | POC SDL type `NodeFilterPayload` (legacy is `NodeFilter`) | weka generated Relay codegen × 2 views (`concreteType: "NodeFilter"`) | Rename SDL type via `@strawberry.type(name="NodeFilter")` decorator |
| C | POC `Table.column_types: [String]` vs legacy `[RowItemType]` | weka × 1, runzi × 1 (`$column_types: [RowItemType]!` in mutation variables) | Add `RowItemType` enum (`integer`/`double`/`string`/`boolean`) and use on both `Table.column_types` and `CreateTableInput.column_types` |
| D | POC `AutomationTask` / `RuptureGenerationTask` / `OpenquakeHazardTask` missing `inversion_solution: InversionSolutionUnion` field | weka `AutomationTaskPage`, `GeneralTaskChildrenTab` | Add `InversionSolutionUnion` and a resolver that picks the `WRITE`-related `InversionSolution` subtype from `files_raw` |

### What the audit confirmed (no action)

- **`InversionSolutionUnion` / `PredecessorUnion`** — no observed
  client query exercises these union types other than via the
  concrete `... on InversionSolution { ... }` fragments. The union
  declarations exist in the POC and are wire-equivalent; no client
  breaks from the SDL difference.
- **Category 2 (input naming)** — no observed query references the
  input type name directly. Wire format identical. Decision stands.
- **Category 3 (auto-generated Edge types)** — no observed query
  references an Edge type by name. Wire format identical. Decision
  stands.

### Lesson added

3. **An ADR drafted from a parity-diff sample needs an audit
   against real client queries before close-out.** ADR-002's
   original Category 1 framing assumed both `Thing` and
   `AutomationTaskInterface` were equally wire-impacting because
   both appeared in the legacy SDL. The client audit refined that:
   `AutomationTaskInterface` is load-bearing; `Thing` is defensive.
   Worse, the audit also surfaced **four breaking divergences this
   ADR didn't catch at all** — they were lurking in the
   "POC-only types" half of the parity diff that we'd partially
   characterised as cosmetic. For future schema ADRs, run the
   client-query audit *before* drafting decisions, not after.

## Related decisions

- [ADR-001](ADR-001-graphql-schema-evolution-strategy.md) — the
  framework this ADR operates within (wire compat as contract,
  modernise where standard has hardened, `@deprecated` to bridge).
- (Future) ADR-003: Custom scalar policy — naming and on-disk
  representation conventions for `DateTime`, `JSONString`, `BigInt`,
  and any future scalars.
- (Future) ADR-004: Deprecation logging and sunset policy — how we
  measure deprecated-field usage and when we remove (ADR-001 Phase 3).
- (Future) ADR-005: snake_case vs camelCase for client-facing
  fields — strategic call on whether to undertake the broader
  migration.
