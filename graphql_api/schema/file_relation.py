import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id

from .file import File
from graphql_api.data_s3 import get_data_manager

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

class FileRole(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    UNDEFINED = "undefined"

class FileRelation(graphene.ObjectType):

    # class Meta:
    #     interfaces = (relay.Node, )
    #'RuptureGenerationTask', '1HGAq8'


    thing = graphene.Field('graphql_api.schema.thing.Thing', required=False)
    file = graphene.Field('graphql_api.schema.schema.FileUnion', required=False)

    role = graphene.Field(FileRole, required=True)

    thing_id = graphene.String()
    file_id = graphene.String()

    @staticmethod
    def resolve_file(root, info, *args, **kwargs):
        # print("FILE", root.file_id)
        return get_data_manager().file.get_one(root.file_id)
        
    @staticmethod
    def resolve_thing(root, info, *args, **kwargs):
        # print("THING", root.thing_id)
        return get_data_manager().thing.get_one(root.thing_id)


class FileRelationConnection(relay.Connection):
    class Meta:
        node = FileRelation

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)

class CreateFileRelation(graphene.Mutation):
    class Arguments:
        thing_id = graphene.ID(required=True)
        file_id = graphene.ID(required=True)
        role = FileRole(required=True)

    ok = graphene.Boolean()
    file_relation = graphene.Field(FileRelation)

    def mutate(self, info, **kwargs):
        t0 = dt.utcnow()
        print("CreateFileRelation.mutate: ", kwargs)
        ftype, file_id = from_global_id(kwargs.pop('file_id'))
        #file = db_root.file.get_one(file_id)
        ttype, thing_id = from_global_id(kwargs.pop('thing_id'))
        #thing = db_root.thing.get_one(kwargs.pop('strong_motion_station_id'))

        file_relation = get_data_manager().file_relation.create('FileRelation', thing_id, file_id, **kwargs)
        db_metrics.put_duration(__name__, 'CreateFileRelation.mutate' , dt.utcnow()-t0)
        return CreateFileRelation(ok=True, file_relation= file_relation)
