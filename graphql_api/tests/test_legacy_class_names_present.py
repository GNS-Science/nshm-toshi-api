"""Ported from graphql_api/tests/object_iteration/test_divine_basedata_class_from_schema_name.py.

Legacy keeps an explicit list of (clazz_name, data_class) tuples used by
its data-layer dispatch. The data_class side is POC-specific (POC uses a
different dispatcher), but the **clazz_name list itself is wire-impacting** —
every name here is a type clients can spread via `... on <Name>` or encode
as a Relay GlobalID prefix. If POC silently dropped one, those queries
break.

This test reads the list verbatim and asserts every name resolves to a
type in POC's SDL.
"""

from graphql_api.schema import schema

# Verbatim from legacy CLASS_MAPPINGS — these are the types clients
# may reference. Sorted + deduped so an addition shows as a real diff.
LEGACY_CLASS_NAMES = sorted(
    set(
        [
            "AggregateInversionSolution",
            "File",
            "GeneralTask",
            "InversionSolution",
            "InversionSolutionNrml",
            "OpenquakeHazardConfig",
            "OpenquakeHazardSolution",
            "OpenquakeHazardTask",
            "RuptureGenerationTask",
            "RuptureSet",
            "ScaledInversionSolution",
            "SmsFile",
            "StrongMotionStation",
            "Table",
            "TimeDependentInversionSolution",
        ]
    )
)


def test_every_legacy_class_name_resolves_in_poc_sdl():
    """A type in the legacy CLASS_MAPPINGS list must exist in POC's SDL.

    Names dropped here become silently-broken fragment spreads in client
    queries.
    """
    sdl = schema.as_str()
    missing = []
    for name in LEGACY_CLASS_NAMES:
        if f"type {name} " not in sdl and f"type {name}\n" not in sdl:
            missing.append(name)
    assert not missing, f"types missing from POC SDL: {missing}"
