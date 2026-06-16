"""Shared clazz_name → type dispatch.

Replaces the three near-identical 14-branch `if clazz == ...` chains in
schema.py (_dispatch_search), models/relations.py (_dispatch_file,
_dispatch_thing). All three iterated the same legacy class names and
called .from_dict on the matched type; the only differences were the
list of valid types per context and the fallback type.

Imports are still done lazily at call time because the Strawberry model
graph has cycles that only resolve at runtime.
"""

import importlib
from typing import Any

# Maps legacy clazz_name → (module path under models/, class name).
# Module is imported lazily on first dispatch to avoid Strawberry
# circular-import issues during schema build.
_CLAZZ_REGISTRY: dict[str, tuple[str, str]] = {
    # Things
    "GeneralTask": ("graphql_api.models.general_task", "GeneralTask"),
    "RuptureGenerationTask": ("graphql_api.models.automation_task", "RuptureGenerationTask"),
    "AutomationTask": ("graphql_api.models.automation_task", "AutomationTask"),
    "StrongMotionStation": ("graphql_api.models.strong_motion_station", "StrongMotionStation"),
    "OpenquakeHazardTask": ("graphql_api.models.openquake_hazard_task", "OpenquakeHazardTask"),
    "OpenquakeHazardSolution": ("graphql_api.models.openquake_hazard_solution", "OpenquakeHazardSolution"),
    "OpenquakeHazardConfig": ("graphql_api.models.openquake_hazard_config", "OpenquakeHazardConfig"),
    # Files
    "ToshiFile": ("graphql_api.models._base.file", "ToshiFile"),
    "SmsFile": ("graphql_api.models.sms_file", "SmsFile"),
    "RuptureSet": ("graphql_api.models.rupture_set", "RuptureSet"),
    "InversionSolution": ("graphql_api.models.inversion_solution", "InversionSolution"),
    "ScaledInversionSolution": ("graphql_api.models.scaled_inversion_solution", "ScaledInversionSolution"),
    "AggregateInversionSolution": ("graphql_api.models.aggregate_inversion_solution", "AggregateInversionSolution"),
    "TimeDependentInversionSolution": (
        "graphql_api.models.time_dependent_inversion_solution",
        "TimeDependentInversionSolution",
    ),
    "InversionSolutionNrml": ("graphql_api.models.inversion_solution_nrml", "InversionSolutionNrml"),
}

# Sets defining which clazz_names are valid in each dispatch context.
# Anything not in the set falls through to the context's default type.
_FILE_CLAZZ_NAMES: frozenset[str] = frozenset(
    {
        "SmsFile",
        "RuptureSet",
        "InversionSolution",
        "ScaledInversionSolution",
        "AggregateInversionSolution",
        "TimeDependentInversionSolution",
        "InversionSolutionNrml",
    }
)

_THING_CLAZZ_NAMES: frozenset[str] = frozenset(
    {
        "RuptureGenerationTask",
        "AutomationTask",
        "StrongMotionStation",
        "OpenquakeHazardTask",
        "OpenquakeHazardSolution",
        "OpenquakeHazardConfig",
    }
)


def _resolve(clazz: str) -> Any:
    """Lazily import and return the Strawberry class for `clazz`."""
    module_path, class_name = _CLAZZ_REGISTRY[clazz]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def dispatch_search(data: dict) -> Any | None:
    """Instantiate any registered type from an ES hit. Returns None for unknown clazz."""
    clazz = data.get("clazz_name", "")
    if clazz not in _CLAZZ_REGISTRY:
        # Default: treat as a plain ToshiFile (matches legacy behaviour).
        return _resolve("ToshiFile").from_dict(data)
    return _resolve(clazz).from_dict(data)


def dispatch_file(data: dict) -> Any:
    """Instantiate the right file-type Strawberry class. Defaults to ToshiFile."""
    clazz = data.get("clazz_name", "")
    if clazz in _FILE_CLAZZ_NAMES:
        return _resolve(clazz).from_dict(data)
    return _resolve("ToshiFile").from_dict(data)


def dispatch_thing(data: dict) -> Any:
    """Instantiate the right thing-type Strawberry class. Defaults to GeneralTask."""
    clazz = data.get("clazz_name", "")
    if clazz in _THING_CLAZZ_NAMES:
        return _resolve(clazz).from_dict(data)
    return _resolve("GeneralTask").from_dict(data)
