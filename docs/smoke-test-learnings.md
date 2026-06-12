# Smoke-Test Learnings — Wire-Format Validation Gaps Found at Client Cutover

**Date written:** 2026-06-12 (mini Phase 4)
**Trigger:** chrisdicaprio's diagnosis after running `nzshm-runzi` against the
deployed Strawberry POC at `/test/graphql-v2`.

## Why this doc exists

When mini Phase 4 (#318) flipped the POC to read-write on the test stage, the
expectation was that our **261-test POC suite** plus **two rounds of manual
client-codebase audit** plus the **schema parity diff tool** would have caught
every wire-format incompatibility before a real client touched the deployed
endpoint.

They didn't. Runzi failed immediately with errors that none of our local tests
had ever produced. This doc captures **why** so we don't make the same call
again on a future migration, sister project, or any time we ship a "drop-in
replacement" of an existing API.

## What broke (round 1 — already fixed in #320)

The first runzi run surfaced two issues that we triaged from the failure
modes:

### Issue A — `post_url` returned `null` on all file-create mutations except `create_rupture_set`

PR #310's Gap 4 closure wired the presigned-POST generation into the
RuptureSet path only. The other six file types (`create_file`,
`create_inversion_solution`, `create_scaled_inversion_solution`,
`create_aggregate_inversion_solution`,
`create_time_dependent_inversion_solution`, `create_inversion_solution_nrml`)
still returned the `FileInterface` default `None`. nshm-toshi-client and runzi
do `json.loads(executed['create_X']['Y']['post_url'])` unconditionally — that
raises `TypeError` on `None`.

**Fix landed in PR #320**: wire `presigned_post_for_file` into the same six
`mutate_create_*` functions. New regression test
`test_post_url_all_file_types.py` (6 tests, one per mutation) pins the
contract.

### Issue B — `create_file` and `create_file_relation` rejected client queries at GraphQL validation time

Legacy SDL exposes these two mutations with **positional arguments**:

```
create_file(file_name: String!, md5_digest: String!, file_size: BigInt!, …): CreateFile
create_file_relation(file_id: ID!, role: FileRole!, thing_id: ID!): CreateFileRelation
```

`nshm-toshi-client` sends them in exactly that shape (verbatim strings now
captured in `test_nshm_toshi_client_compat.py`). The POC had wrapped both in
`CreateFileInput!` / `CreateFileRelationInput!`, so the client's query failed
at validation with `Unknown argument 'file_name' on field 'create_file'`.

**Fix landed in PR #320**: realign both POC mutations to the legacy
positional shape. The `CreateFileInput` / `CreateFileRelationInput` dataclasses
remain for internal pipe-through; Strawberry drops unused
`@strawberry.input` types from the SDL. New regression tests pin the wire
shape against the exact strings `nshm-toshi-client` sends.

### What we shipped vs what was still wrong

Runtime + suite status after #320:

- ✅ 261 tests passing
- ✅ Two specific issues runzi hit are closed
- ❌ A larger systemic gap (covered in §"Round 2" below) was undetected by our
  testing regime even after the round-1 fixes landed

## Why our testing regime didn't catch any of this

Five distinct holes, in roughly order of severity. These are the *systemic*
findings — not the individual mutations that need fixing.

### 1. Tests validated the POC against ITSELF, not against legacy

Our 261 POC tests write mutation strings like:

```graphql
mutation X($input: CreateGeneralTaskInput!) { 
  create_general_task(input: $input) { … }
}
```

The variable type `$input: CreateGeneralTaskInput!` is **the POC's input
type**. The test asserts that the POC schema accepts the POC's idea of the
input. It always will. The runzi-style query that declares
`$argument_lists: [KeyValueListPairInput]!` (legacy-style nullable elements)
never gets exercised by our test suite at all.

GraphQL's type checker rejects variables when the variable type is wider than
the position type — `[T]` cannot supply a `[T!]` position — but only when a
client actually sends one. Our tests never sent that combination.

### 2. The schema-parity tool flagged the issues; we accepted them

`spike/strawberry_poc/tools/schema_parity.py` exists and was run in past
sessions. It surfaced `[T] → [T!]` mismatches alongside other divergences. In
ADR-002 §3a we categorized those as "documented divergence — wire-equivalent":

> "Wire-equivalence is not SDL-equivalence. `[X]` vs `[X!]` produce identical
> JSON on the wire for the same data."

That's true for **response data** (the JSON for a list of three items is the
same regardless of element-nullability). It is **NOT** true for **input
variables** — GraphQL's variable-type subsumption check rejects the wider
type going into a narrower position at validation time, before any data
flows.

We conflated the response side with the input side. ADR-002 needs an update;
this conflation is the load-bearing wrong call from the first audit.

### 3. The "verbatim client query" regression tests covered too few mutations

After the ADR-002 client-divergence audit we wrote `test_weka_parity.py` and
later `test_nshm_toshi_client_compat.py` with copy-pasted query strings.
That hit ~6 mutations. Runzi sends ~20. The ones with list-typed variables
(`argument_lists`, `predecessors`, `source_solutions`, `fault_models`,
`column_types`, `rows`, …) weren't in the hand-picked set, so the
`[T]` → `[T!]` regression had no chance of surfacing.

### 4. The schema-parity tool isn't a CI gate

Even when the tool surfaced things, no workflow step ran it with
`--fail-on-diff` to block merges. So divergence accumulated quietly — every
new `list[T]` field in a POC PR added another `[T!]` to the SDL without any
CI signal. Drift was silent.

### 5. The Strawberry → SDL transformation has a non-obvious gotcha

Strawberry: `list[T]` → SDL `[T!]`
Graphene (legacy): `list[T]` → SDL `[T]`

Same Python signature, different library defaults. To force Strawberry to
emit `[T]` you have to write `list[T | None]` — which is semantically weird
(you're not saying "the list may contain `None`" in the application sense;
you're hacking the SDL emission to match Graphene's default).

That gotcha lived in nobody's head; not in any contributor's checklist; not
in the ADR. Every new input field with a list type was a chance to silently
regress.

## The single-line answer

> We tested that **the POC works**, not that **the POC is wire-compatible with
> legacy**. Those are different properties; we only had robust evidence of
> the first.

## What we're changing going forward (round 2 — comprehensive parity PR)

| Gap | Fix in the upcoming parity PR |
|---|---|
| Tests didn't validate against legacy-style queries | Auto-extract every mutation/query string from `LIB/nshm-toshi-client/`, `MISC/nzshm-runzi/runzi/automation/toshi_api/`, and weka, and assert each one validates *and* executes against the POC schema. Replaces the ad-hoc hand-picked verbatim approach. |
| Tool surfaced issues, decision wrong | Update ADR-002 §3a: list-element nullability moves from "accepted divergence" to "wire-breaking". Connection-type renames (`FileRelationConnection` etc) likewise. |
| Hand-picked verbatim coverage too narrow | Replaced by the auto-extracted approach above. |
| No CI gate | Add a `schema_parity.py --fail-on-diff` step to the `strawberry-poc-tests` workflow. Exit code is the gate — no merge if SDL diverges. |
| Implicit Strawberry SDL transformation | Add a `tests/test_sdl_emission_invariants.py` that asserts `list[T]` never emits `[T!]` in any `@strawberry.input` class. Pure SDL inspection, runs as a unit test. Cheap, explicit, and acts as a contributor reminder. |

## Outstanding issues round 2 surfaced (to be addressed in the comprehensive parity PR)

Quantified via the schema-parity tool:

- **87 list-element nullability mismatches** (34 in `@strawberry.input` types,
  blocks every client query that declares a list-typed variable; 60 on
  output types, affects clients with typed bindings).
- **~118 other field type mismatches**, including:
  - Connection type renames (`FileRelationsConnection` →
    `FileRelationConnection`, `TaskRelationsConnection` →
    `TaskTaskRelationConnection`).
  - `create_task_relation` still uses `input:` wrapper (sibling to
    `create_file_relation` which PR #320 fixed; this one was missed).
  - OQ task payload field `openquake_hazard_task` vs POC's `task_result`.
  - `LabelledTableRelation` missing `table { id }` field.
  - `CreateInversionSolutionInput` missing `mfd_table_id`.
  - Several `String!` → `String` and `DateTime` → `String` reverts on input
    classes.

## Future-self checklist

When shipping a "drop-in replacement" of an existing API in future:

1. **Define "drop-in" precisely.** It's not "the tests pass"; it's "every real
   client query parses, validates, and executes against the new API". If your
   acceptance criterion can be derived from the new API alone, you're testing
   self-consistency, not compatibility.

2. **Extract client queries automatically.** Don't trust manual code-audit
   grepping. Walk every client codebase, harvest every mutation/query string,
   submit them all to the new schema. The number to track is "how many of
   the N client queries validate today?".

3. **Treat the schema parity tool's output as binding.** If a mismatch is in
   the report, it requires either a fix or an ADR entry explicitly listing
   the affected client behaviour. "Wire-equivalent" is not a free pass — it's
   wire-equivalent for *response data* but not necessarily for *input
   variables* or *fragment patterns*.

4. **Add a CI gate.** No diff = no merge. Otherwise drift accumulates
   silently between PRs.

5. **Capture the framework-specific gotchas in writing.** Strawberry's
   `list[T] → [T!]` default is one example; there are others (default values,
   description text, scalar coercion behaviour). Write them down somewhere
   contributors actually read.

## References

- PR #318 — mini Phase 4 (the flip that surfaced this)
- PR #320 — round 1 fixes (post_url + positional args)
- (Upcoming) PR — round 2 comprehensive parity fixes + CI gate + ADR-002
  update
- ADR-002 §3a — the audit footer that conflated wire-equivalence with
  input-variable type-system equivalence
- ADR-004 — code reorganization (separate gating decision)
- `spike/strawberry_poc/tools/schema_parity.py` — the parity tool
