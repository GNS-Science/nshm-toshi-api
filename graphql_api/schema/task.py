import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload
from graphene import Enum

global db_root


class TaskResult(Enum):
    FAILURE = "fail"
    SUCCESS = "success"
    UNDEFINED = None

class TaskState(Enum):
    SCHEDULED = "scheduled"
    STARTED = "started"
    DONE = "done"
    UNDEFINED = None

class Task(graphene.Interface):
    """A Task in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, )

    result = TaskResult()
    state = TaskState()

    started = graphene.DateTime(description="The time the task was started")
    duration = graphene.Float(description="the final duraton of the task in seconds")

    files = relay.ConnectionField(
         'graphql_api.schema.task_file.TaskFileConnection', description="Files associated with this task."
    )

    def resolve_files(self, info, **args):
        # Transform the instance ship_ids into real instances
        return [db_root.task_file.get_one(_id) for _id in self.files]




