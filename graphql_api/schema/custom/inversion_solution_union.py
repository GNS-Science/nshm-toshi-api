# !inversion_solution_union.py
import graphene

from .aggregate_inversion_solution import AggregateInversionSolution
from .inversion_solution import InversionSolution
from .scaled_inversion_solution import ScaledInversionSolution
from .time_dependent_inversion_solution import TimeDependentInversionSolution


class InversionSolutionUnion(graphene.Union):
    class Meta:
        types = (
            InversionSolution,
            ScaledInversionSolution,
            AggregateInversionSolution,
            TimeDependentInversionSolution,
        )
