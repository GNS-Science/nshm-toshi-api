import graphene
from graphene import relay
from graphene import Enum

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
