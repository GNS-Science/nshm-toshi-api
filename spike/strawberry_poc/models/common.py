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


# ── Task enums ────────────────────────────────────────────────────────────────
# Values match the production Graphene schema (lowercase stored values).

@strawberry.enum
class TaskSubType(enum.Enum):
    RUPTURE_SET = "rupture_set"
    INVERSION = "inversion"
    HAZARD = "hazard"
    DISAGG = "disagg"
    REPORT = "report"
    SCALE_SOLUTION = "scale_solution"
    AGGREGATE_SOLUTION = "aggregate_solution"
    SOLUTION_TO_NRML = "solution_to_nrml"
    OPENQUAKE_HAZARD = "openquake_hazard"
    TIME_DEPENDENT_SOLUTION = "time_dependent_solution"
    UNDEFINED = "undefined"


@strawberry.enum
class ModelType(enum.Enum):
    CRUSTAL = "crustal"
    SUBDUCTION = "subduction"
    COMPOSITE = "composite"


@strawberry.enum
class EventResult(enum.Enum):
    FAILURE = "fail"
    PARTIAL = "partial"
    SUCCESS = "success"
    UNDEFINED = "undefined"


@strawberry.enum
class EventState(enum.Enum):
    SCHEDULED = "scheduled"
    STARTED = "started"
    DONE = "done"
    UNDEFINED = "undefined"


# ── File relation enums ───────────────────────────────────────────────────────

@strawberry.enum
class FileRole(enum.Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    UNDEFINED = "undefined"


# ── SMS / StrongMotionStation enums ───────────────────────────────────────────

@strawberry.enum
class SmsSiteClass(enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


@strawberry.enum
class SmsSiteClassBasis(enum.Enum):
    Vs = "Vs"
    SPT = "SPT"
    su = "su"


@strawberry.enum
class SmsFileType(enum.Enum):
    BH = "bh"
    CPT = "cpt"
    DH = "dh"
    HVSR = "hvsr"
    SW = "sw"


# ── Openquake / hazard enums ──────────────────────────────────────────────────

@strawberry.enum
class OpenquakeTaskType(enum.Enum):
    HAZARD = "hazard"
    DISAGG = "disagg"
    UNDEFINED = "undefined"


@strawberry.enum
class AggregationFn(enum.Enum):
    MEAN = "mean"


@strawberry.enum
class TableType(enum.Enum):
    HAZARD_GRIDDED = "hazard_gridded"
    HAZARD_SITES = "hazard_sites"
    MFD_CURVES = "mfd_curves"
    MFD_CURVES_V2 = "mfd_curves_v2"
    GENERAL = "general"


@strawberry.enum
class AncestryLabel(enum.Enum):
    SIBLING = 0
    PARENT = -1
    GRANDPARENT = -2
    GREAT_GRANDPARENT = -3
    GREAT_GREAT_GRANDPARENT = -4
