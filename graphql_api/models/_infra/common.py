"""Shared scalar types and enums used across schema types."""

import enum
from typing import NewType

import strawberry


def _try_enum[E: enum.Enum](enum_cls: type[E], value: str | None) -> E | None:
    """Construct an enum from a string value, returning None for unknown/missing values."""
    if value is None:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


# ── Custom scalars ────────────────────────────────────────────────────────────

BigInt = strawberry.scalar(
    NewType("BigInt", int),
    serialize=int,
    parse_value=int,
    description="A signed integer with arbitrary precision (not limited to GraphQL Int 32-bit). "
    "Used for file_size where production values can exceed 2GB.",
)


def _parse_datetime(value):
    """Validate an inbound DateTime value, matching legacy Graphene semantics:
      - must parse as ISO 8601
      - must be timezone-aware (naive datetimes are rejected)
    Returns the string unchanged so downstream resolvers see a `str` (the rest
    of the codebase treats DateTime values as strings end-to-end).
    """
    import datetime as _dt  # noqa: PLC0415

    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("DateTime value must have a timezone (naive datetimes are rejected)")
        return value.isoformat()
    s = str(value)
    try:
        parsed = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"DateTime value {value!r} is not a valid ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise ValueError("DateTime value must have a timezone (naive datetimes are rejected)")
    return s


# ADR-001 Phase 1: restore the legacy typed scalars. Wire format is an ISO 8601
# string (DateTime) or a JSON-encoded string (JSONString). Python type stays as
# `str` so we don't force every resolver to construct typed values; the scalar
# rename is what fixes typed-client codegen parity with legacy.
DateTime = strawberry.scalar(
    NewType("DateTime", str),
    serialize=str,
    parse_value=_parse_datetime,
    description="An ISO 8601 datetime string with timezone. Wire-compatible "
    "with the legacy graphene DateTime scalar (which rejected naive and "
    "malformed values); typed clients get a `DateTime` rather than a "
    "plain `String`.",
)

JSONString = strawberry.scalar(
    NewType("JSONString", str),
    serialize=str,
    parse_value=str,
    description="A JSON-encoded string. Wire-compatible with the legacy graphene "
    "JSONString scalar; used for embedded JSON payloads like Openquake logic trees.",
)


# ADR-001 Phase 1: Relay 1 clientMutationId backwards-compatibility.
# Every mutation input and payload exposes `clientMutationId: String` as a
# deprecated field. Inputs accept it (legacy Relay 1 clients send it); payloads
# echo it back (legacy clients read it). Modern Relay 2 / Apollo / urql clients
# can omit it entirely. Helpers below return fresh strawberry.field metadata so
# each class definition gets its own field instance (Strawberry's field()
# returns mutable metadata, sharing it across classes confuses the framework).


def client_mutation_id_input_field():
    """Field metadata for `clientMutationId: String` on mutation INPUT types.

    Accepted from Relay 1 clients; passed through to the payload unchanged.
    Marked deprecated so introspection / IDE autocomplete shows a warning.
    """
    return strawberry.field(
        name="clientMutationId",
        default=None,
        deprecation_reason=(
            "Relay 1 ClientIDMutation holdover — modern Relay 2 / Apollo / urql clients "
            "can omit this. When provided, the value is echoed back unchanged in the "
            "mutation payload's clientMutationId field."
        ),
    )


def client_mutation_id_payload_field():
    """Field metadata for `clientMutationId: String` on mutation PAYLOAD types.

    Echoes back the value from the input when provided. Marked deprecated.
    """
    return strawberry.field(
        name="clientMutationId",
        default=None,
        deprecation_reason=(
            "Relay 1 ClientIDMutation holdover — echoes the value passed to the input's "
            "clientMutationId field, or null if none was sent. Modern Relay 2 / Apollo / "
            "urql clients can ignore."
        ),
    )


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
    v: list[str | None] | None = None


@strawberry.input
class KeyValueListPairInput:
    k: str
    # `v` matches legacy `[String]` exactly — nullable outer list, nullable
    # elements — so client variables typed `[String]!` validate at this
    # position. See docs/smoke-test-learnings.md §1.
    v: list[str | None] | None = None


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
class RowItemType(enum.Enum):
    integer = "INT"
    double = "DBL"
    string = "STR"
    boolean = "BOO"


@strawberry.enum
class AncestryLabel(enum.Enum):
    SIBLING = 0
    PARENT = -1
    GRANDPARENT = -2
    GREAT_GRANDPARENT = -3
    GREAT_GREAT_GRANDPARENT = -4
