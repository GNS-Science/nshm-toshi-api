"""InversionSolutionUnion — the IS produced by an AutomationTask family member.

Mirrors legacy `inversion_solution_union.py`. Used by AutomationTask,
RuptureGenerationTask, and OpenquakeHazardTask to expose the WRITE-related
inversion solution file as a first-class field.
"""

from typing import Annotated

import strawberry

from graphql_api.data.dynamo import get_file

from graphql_api.models._infra.common import FileRole

_InversionSolution = Annotated["InversionSolution", strawberry.lazy("graphql_api.models.inversion_solution")]
_ScaledInversionSolution = Annotated["ScaledInversionSolution", strawberry.lazy("graphql_api.models.scaled_inversion_solution")]
_AggregateInversionSolution = Annotated[
    "AggregateInversionSolution", strawberry.lazy("graphql_api.models.aggregate_inversion_solution")
]
_TimeDependentInversionSolution = Annotated[
    "TimeDependentInversionSolution", strawberry.lazy("graphql_api.models.time_dependent_inversion_solution")
]


InversionSolutionUnion = Annotated[
    _InversionSolution | _ScaledInversionSolution | _AggregateInversionSolution | _TimeDependentInversionSolution,
    strawberry.union(name="InversionSolutionUnion"),
]


_IS_CLAZZ_DISPATCH = {
    "InversionSolution": "graphql_api.models.inversion_solution",
    "ScaledInversionSolution": "graphql_api.models.scaled_inversion_solution",
    "AggregateInversionSolution": "graphql_api.models.aggregate_inversion_solution",
    "TimeDependentInversionSolution": "graphql_api.models.time_dependent_inversion_solution",
}


def resolve_task_inversion_solution(dynamodb, files_raw: list | None):
    """Find the InversionSolution produced (file_role=WRITE) by a task.

    Mirrors legacy `AutomationTask.resolve_inversion_solution` traversal:
    iterate file relations, pick the WRITE one whose file is an
    InversionSolution subtype.
    """
    if not files_raw:
        return None
    import importlib  # noqa: PLC0415

    for entry in files_raw:
        if not isinstance(entry, dict):
            continue
        if entry.get("file_role") != FileRole.WRITE.value:
            continue
        file_id = entry.get("file_id")
        if not file_id:
            continue
        data = get_file(dynamodb, file_id)
        if not data:
            continue
        clazz = data.get("clazz_name", "")
        module_path = _IS_CLAZZ_DISPATCH.get(clazz)
        if not module_path:
            continue
        module = importlib.import_module(module_path)
        cls = getattr(module, clazz)
        return cls.from_dict(data)
    return None
