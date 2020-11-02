"""
The NSHM data file graphql schema.
"""
import graphene
from graphene import relay
from .task_result import TaskResult
from .data_file import File

global db_root

class TaskFile(graphene.ObjectType):
    """A File used in some Task """
    class Meta:
        interfaces = (relay.Node, )

    task = graphene.Field(TaskResult, required=True)
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
