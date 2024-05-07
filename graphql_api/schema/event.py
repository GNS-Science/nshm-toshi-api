import graphene
from graphene import Enum, relay

global db_root


class EventResult(Enum):
    FAILURE = "fail"
    PARTIAL = "partial"
    SUCCESS = "success"
    UNDEFINED = "undefined"


class EventState(Enum):
    SCHEDULED = "scheduled"
    STARTED = "started"
    DONE = "done"
    UNDEFINED = "undefined"
