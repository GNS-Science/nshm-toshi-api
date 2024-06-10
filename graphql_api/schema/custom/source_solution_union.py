import graphene

from .inversion_solution import InversionSolution
from .time_dependent_inversion_solution import TimeDependentInversionSolution
from .scaled_inversion_solution import ScaledInversionSolution
from .aggregate_inversion_solution import AggregateInversionSolution

class SourceSolutionUnion(graphene.Union):
    class Meta:
        types = (AggregateInversionSolution, InversionSolution, ScaledInversionSolution, TimeDependentInversionSolution)

