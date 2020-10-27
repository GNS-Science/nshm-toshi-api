import graphene
from graphene import relay
from graphene_file_upload.scalars import Upload

from .data_s3 import TaskResultData, get_faction

class TaskResult(graphene.ObjectType):
    """A TaskResult in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the TaskResult.")

    @classmethod
    def get_node(cls, info, id):
        return db_root.get_one(id)

class TaskResultConnection(relay.Connection):
    class Meta:
        node = TaskResult

class Faction(graphene.ObjectType):
    """A faction in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the faction.")
    task_results = relay.ConnectionField(
        TaskResultConnection, description="The TaskResults used by the faction."
    )

    def resolve_task_results(self, info, **args):
        # Transform the instance task_result_ids into real instances
        return [db_root.get_one(task_result_id) for task_result_id in self.task_results]

    @classmethod
    def get_node(cls, info, id):
        return get_faction(id)


class CreateTaskResult(relay.ClientIDMutation):
    class Input:
        task_result_name = graphene.String(required=True)
        faction_id = graphene.String(required=True)

    task_result = graphene.Field(TaskResult)
    faction = graphene.Field(Faction)

    @classmethod
    def mutate_and_get_payload(cls, root, info, task_result_name, faction_id, client_mutation_id=None):
        task_result = db_root.create(task_result_name, faction_id)
        faction = get_faction(faction_id)
        return CreateTaskResult(task_result=task_result, faction=faction)


class ToshUploadMutation(graphene.Mutation):
    class Arguments:
        file_in = Upload(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, file_in, **kwargs):
        # do something with your file
        for line in file_in:
            print(line)
        return ToshUploadMutation(ok=True)

class Query(graphene.ObjectType):
    task_results = relay.ConnectionField(
        TaskResultConnection, description="The TaskResults used by the faction."
    )
    task_result = graphene.Field(TaskResult)
    node = relay.Node.Field()

    def resolve_task_result(root, info):
        return db_root.get_one()

    def resolve_task_results(root, info):
        return db_root.get_all()

class Mutation(graphene.ObjectType):
    create_task_result = CreateTaskResult.Field()
    my_upload= ToshUploadMutation.Field()

db_root = TaskResultData()
schema = graphene.Schema(query=Query, mutation=Mutation)
