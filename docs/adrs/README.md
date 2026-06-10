# Architecture Decision Records

This directory captures significant architectural decisions for the
`nshm-toshi-api` project — the *why* behind structural choices that
are expensive to reverse and that future maintainers (including future
us) will otherwise have to reverse-engineer.

## When to write an ADR

Write an ADR when the choice:

1. Affects the **API contract** seen by clients (weka, runzi, downstream
   tooling).
2. Imposes a **cross-cutting constraint** that future contributors need
   to be aware of even if they don't touch the originating code.
3. Required **non-trivial analysis** to land on, and the analysis itself
   is the durable artifact (not just the decision).
4. Would be hard to **reverse without a deprecation cycle**.

Examples that warrant an ADR:
- "Why do we have a custom `BigInt` scalar instead of `Int`?"
- "Why do mutation payloads include a deprecated `clientMutationId`?"
- "Why is the Strawberry POC scoped under `spike/` rather than top-level?"

Examples that don't:
- Small refactors, bugfixes, dependency upgrades.
- "Why did we name this function `_try_enum`?" (live with the code.)
- Strategy docs that are explorations rather than decisions (those go
  in `docs/` directly, see `ALTERNATE_STACK_QUESTIONS.md`).

## Format

ADRs follow a slight adaptation of [Michael Nygard's
template](https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md),
extended for our project style:

```
# ADR-NNN: <Short title in title case>

## Status
Proposed | Accepted | Superseded by ADR-NNN | Deprecated

## Context
The problem and the relevant constraints. Include enough domain
context that a new contributor 12 months from now will understand
the situation without spelunking commits.

## Decision
The choice we made. State it clearly enough that future readers can
tell whether their case falls inside or outside the decision's scope.

## Consequences
The positives and negatives, including known trade-offs. List items
this decision blocks, enables, or makes harder.

## Related decisions
Cross-links to other ADRs.
```

When a decision touches multiple distinct areas (e.g. naming,
scalars, deprecation policy), feel free to add a `## Specific
decisions` section with a table — see
`ADR-001-graphql-schema-evolution-strategy.md`.

## Numbering and filename

Sequential, three-digit, zero-padded. Filename pattern:

```
ADR-NNN-{descriptive-name-in-kebab-case}.md
```

For example: `ADR-001-graphql-schema-evolution-strategy.md`.

Once a number is assigned it never changes — even if an ADR is
superseded (mark it `Superseded by ADR-NNN` in the Status section and
leave the file in place).

## Index

| # | Title | Status |
|---|---|---|
| [ADR-001](ADR-001-graphql-schema-evolution-strategy.md) | GraphQL Schema Evolution Strategy: Legacy Parity, Modern Defaults, Deprecation Aliases | Proposed |
| [ADR-002](ADR-002-schema-interface-hierarchy-and-input-naming.md) | Schema Interface Hierarchy and Input Naming Conventions | Accepted |
| [ADR-003](ADR-003-cognito-permission-model.md) | Cognito Permission Model: Two Axes and a Cumulative AWS Ladder | Accepted |