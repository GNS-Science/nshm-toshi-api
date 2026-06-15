"""Validates the vendored runzi GraphQL query corpus against POC's SDL.

This is the durable answer from docs/smoke-test-learnings.md future-self
item #2 — every embedded GraphQL operation in runzi's `toshi_api`
package gets validated against POC's schema, end of story.

## Why vendored, not live

The corpus is a SNAPSHOT — see `tests/data/runzi_corpus.py`. The
snapshot lives in this repo for two reasons:

1. **CI runs without external dependencies.** The original
   live-extraction approach assumed a sibling MISC/nzshm-runzi clone
   on the filesystem; CI runners don't have that. Vendoring removes
   the cross-repo dependency.

2. **Tests pin to a specific runzi commit.** When the snapshot fixes
   a runzi query, we know exactly which runzi commit it landed in.

To refresh the snapshot when runzi changes:

    python spike/strawberry_poc/tools/refresh_runzi_corpus.py

## Long-term plan (Option 4)

The right home for "runzi queries validate against the toshi-api SDL"
is on the runzi side — weka and kororaa already do this, both keep a
copy of `schema.graphql` and run codegen/validation against it as
part of their own build. See runzi#308 for the ticket asking runzi
to follow suit. When runzi adopts that pattern, this corpus test +
the vendored fixture can be deleted.
"""

import importlib.util
from pathlib import Path

import pytest
from graphql import parse, validate

from schema import schema


# `tests/` is not a Python package (adding an __init__.py here breaks the
# rest of the suite, which relies on sys.path-based imports). Load the
# fixture by file path instead.
_fixture_path = Path(__file__).parent / "runzi_corpus_data.py"
_spec = importlib.util.spec_from_file_location("runzi_corpus_data", _fixture_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
OPERATIONS = _module.OPERATIONS


# Runzi has a couple of queries that select fields nobody implements
# (`source_solution` on LabelledTableRelation never existed in legacy
# either) or that exploit graphene's non-spec-compliant union/interface
# field auto-resolution. These are runzi bugs, not POC parity gaps —
# they were filed upstream as runzi#307. Recording them here means the
# corpus check stays accurate without surfacing them as POC failures.
#
# Delete entries from this set as runzi#307 closes them.
_RUNZI_KNOWN_BAD = {
    # `tables { source_solution }` — LabelledTableRelation has never had this field.
    "Cannot query field 'source_solution' on type 'LabelledTableRelation'.",
    # `source_models { id }` on OpenquakeNrmlUnion — graphene-lenient,
    # strict GraphQL spec rejects (clients need inline-fragment per the spec).
    "Cannot query field 'id' on type 'OpenquakeNrmlUnion'.",
}


def test_corpus_is_non_empty():
    """Sanity: the vendored fixture has operations. Catches an empty refresh."""
    assert OPERATIONS, (
        "Vendored runzi corpus is empty. Either the refresh script broke "
        "(re-run tools/refresh_runzi_corpus.py) or runzi has no queries "
        "left to validate (in which case this whole test file can be deleted)."
    )


@pytest.mark.parametrize(
    "origin,query",
    OPERATIONS,
    ids=[label for label, _ in OPERATIONS],
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
