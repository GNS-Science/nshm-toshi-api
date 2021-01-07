import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id

from graphql_api.data_s3 import get_data_manager
from graphql_api.schema.custom import (GeneralTask, RuptureGenerationTask)

class ChildTaskUnion(graphene.Union):
    class Meta:
        types = (GeneralTask, RuptureGenerationTask)

class TaskTaskRelation(graphene.ObjectType):

    class Meta:
        interfaces = (relay.Node, )

    parent = graphene.Field(GeneralTask, required=True)
    child = graphene.Field(ChildTaskUnion, required=True)

    parent_id = graphene.String()
    child_id = graphene.String()

class TaskTaskRelationConnection(relay.Connection):
    class Meta:
        node = TaskTaskRelation

class CreateTaskTaskRelation(graphene.Mutation):
    class Arguments:
        parent_id = graphene.ID(required=True)
        child_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    thing_relation = graphene.Field(TaskTaskRelation)

    def mutate(self, info, **kwargs):
        print("CreateTaskTaskRelation.mutate: ", kwargs)
        ftype, parent_id = from_global_id(kwargs.pop('parent_id'))
        ttype, child_id = from_global_id(kwargs.pop('child_id'))

        thing_relation = get_data_manager().thing_relation.create('TaskTaskRelation', parent_id, child_id, **kwargs)
        return CreateTaskTaskRelation(ok=True, thing_relation=thing_relation)
