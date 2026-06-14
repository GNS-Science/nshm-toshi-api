"""Auto-extracted client-query corpus from MISC/nzshm-runzi.

This is the durable answer documented in docs/smoke-test-learnings.md
future-self checklist item #2 — instead of hand-picking queries to
test verbatim, walk the client codebase and validate every embedded
GraphQL operation against POC's schema.

If POC validates them all, runzi can talk to POC without breaking on
the wire. Each new gap that ever ships gets caught here automatically.
"""

import re
from pathlib import Path

import pytest
from graphql import parse, validate

from schema import schema


# Anchor relative to the repo root: this file lives at
# spike/strawberry_poc/tests/, so .parents[3] is the nshm-toshi-api repo,
# and the sibling runzi clone is up two more levels under MISC/.
_RUNZI_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".."
    / ".."
    / "MISC"
    / "nzshm-runzi"
    / "runzi"
    / "automation"
    / "toshi_api"
).resolve()


# A triple-quoted block whose first non-whitespace token is `query`,
# `mutation`, or `fragment`. Permissive on whitespace and the operation
# name so we catch runzi's typical `qry = '''mutation foo (…) {…}'''`.
_GQL_LITERAL = re.compile(
    r"'''(\s*(?:query|mutation|fragment)\b[^']*?)'''",
    re.DOTALL,
)


def _has_unresolved_placeholders(op: str) -> bool:
    """Runzi uses ###NAME### tokens that get string-substituted before send.

    The static extractor can't resolve them; skip those queries so we test
    only the parts where the literal IS the real query.
    """
    return "###" in op or "##" in op


def _extract_operations():
    """Yield (origin, operation_text) tuples from every .py under runzi/toshi_api."""
    if not _RUNZI_ROOT.is_dir():
        return  # explicit skip handled at test collection time
    for py in sorted(_RUNZI_ROOT.rglob("*.py")):
        text = py.read_text(encoding="utf-8")
        for m in _GQL_LITERAL.finditer(text):
            op = m.group(1).strip()
            if _has_unresolved_placeholders(op):
                continue
            # Cheap label: file_basename:opening_line
            first_line = op.splitlines()[0] if op else ""
            label = f"{py.relative_to(_RUNZI_ROOT.parent.parent.parent)}::{first_line[:60]}"
            yield label, op


_OPERATIONS = list(_extract_operations())


# Runzi has a couple of queries that select fields nobody implements (`source_solution`
# on LabelledTableRelation never existed in legacy either) or that exploit
# graphene's non-spec-compliant union/interface field auto-resolution.
# These are runzi bugs, not POC parity gaps — we record them so the corpus
# test stays accurate without surfacing them as POC failures.
_RUNZI_KNOWN_BAD = {
    # `tables { source_solution }` — LabelledTableRelation has never had this field.
    "Cannot query field 'source_solution' on type 'LabelledTableRelation'.",
    # `source_models { id }` on OpenquakeNrmlUnion — graphene-lenient,
    # strict GraphQL spec rejects (clients need inline-fragment per the spec).
    "Cannot query field 'id' on type 'OpenquakeNrmlUnion'.",
}


def test_runzi_clone_is_discoverable():
    """If the runzi sibling repo isn't checked out, fail loudly."""
    assert _RUNZI_ROOT.is_dir(), (
        f"runzi clone not found at {_RUNZI_ROOT}. "
        "Clone GNS-Science/nzshm-runzi into ../../MISC/nzshm-runzi so this "
        "corpus test can find real client queries."
    )


def test_extracted_at_least_some_operations():
    """Sanity: we found something. Catches an empty-regex / wrong-path silent pass."""
    assert _OPERATIONS, (
        "runzi corpus extracted ZERO operations. Either the regex went wrong "
        "or runzi's query shape changed (e.g. moved to a different package)."
    )


@pytest.mark.parametrize(
    "origin,query",
    _OPERATIONS or [("placeholder", "query Empty { __typename }")],
    ids=[label for label, _ in _OPERATIONS] or ["placeholder"],
)
def test_runzi_query_validates_against_poc(origin, query):
    """Every runzi-embedded GraphQL operation must validate against POC's schema.

    `validate()` runs the full GraphQL spec validation: field existence,
    argument types, variable-type subsumption, fragment spreads, etc.
    No execution happens — no DynamoDB needed. Failures here are
    schema-layer parity gaps.
    """
    document = parse(query)
    errors = validate(schema._schema, document)
    # Strip out errors that match runzi-own bugs (see _RUNZI_KNOWN_BAD).
    real_errors = [
        e for e in errors
        if not any(known in e.message for known in _RUNZI_KNOWN_BAD)
    ]
    assert not real_errors, (
        f"{origin}\n"
        + "\n".join(f"  - {e.message}" for e in real_errors)
        + "\n\n"
        + (query[:400] + ("..." if len(query) > 400 else ""))
    )
