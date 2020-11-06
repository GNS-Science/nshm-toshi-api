"""
The NSHM data file graphql schema.
"""
import graphene
from graphene import relay
from .task import Task
from .file import File

from graphene import Enum

global db_root

class TaskFileRole(Enum):
    READ = "read"
    write = "write"
    READ_WRITE = "read_write"

class TaskFile(graphene.ObjectType):
    """A File used in some Task """
    class Meta:
        interfaces = (relay.Node, )

    task_role = TaskFileRole(required=True)
    task = graphene.Field(Task, required=True)
    file = graphene.Field(File, required=True)

    @classmethod
    def get_node(cls, info, _id):
        return db_root.task_file.get_one(_id)


class CreateTaskFile(graphene.Mutation):
    class Arguments:
        task_id = graphene.ID(required=True)
        file_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    task_file = graphene.Field(TaskFile)

    def mutate(self, info, **kwargs):
        print("CreateTaskFile.mutate: ", kwargs)
        task_file = db_root.task_file.create(**kwargs)
        return CreateTaskFile(ok=True, task_file=task_file)

class TaskFileConnection(relay.Connection):
    """A Relay connection listing Files"""
    class Meta:
        node = TaskFile
