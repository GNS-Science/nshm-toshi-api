"""Shared scalar types and enums used across schema types."""
import enum

import strawberry


@strawberry.type
class KeyValuePair:
    k: str
    v: str


@strawberry.input
class KeyValuePairInput:
    k: str
    v: str


@strawberry.type
class KeyValueListPair:
    k: str
    v: list[str]


@strawberry.input
class KeyValueListPairInput:
    k: str
    v: list[str]


@strawberry.enum
class TaskSubType(enum.Enum):
    INVERSION = "INVERSION"
    HAZARD = "HAZARD"
    AGGREGATE = "AGGREGATE"
    SCALE_SOLUTION = "SCALE_SOLUTION"
    OTHER = "OTHER"


@strawberry.enum
class ModelType(enum.Enum):
    CRUSTAL = "CRUSTAL"
    SUBDUCTION_INTERFACE = "SUBDUCTION_INTERFACE"
    SUBDUCTION_INTRASLAB = "SUBDUCTION_INTRASLAB"
    COMPOSITE = "COMPOSITE"
