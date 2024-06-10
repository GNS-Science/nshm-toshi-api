import graphene

from .aggregate_inversion_solution import AggregateInversionSolution
from .inversion_solution import InversionSolution
from .scaled_inversion_solution import ScaledInversionSolution
from .time_dependent_inversion_solution import TimeDependentInversionSolution


class SourceSolutionUnion(graphene.Union):
    class Meta:
        types = (AggregateInversionSolution, InversionSolution, ScaledInversionSolution, TimeDependentInversionSolution)
