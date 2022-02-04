import graphene
from graphene import relay
from graphene import Enum
from graphql_relay import from_global_id
from graphql_api.schema.file_relation import FileRelationConnection
from graphql_api.data_s3 import get_data_manager

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

class Thing(graphene.Interface):
    """A Thing in the NSHM saga"""
    class Meta:
        interfaces = (relay.Node, )

    created = graphene.DateTime(description="When the thing was created")

    files = relay.ConnectionField(
         FileRelationConnection, description="Files associated with this object."
    )

    def resolve_files(root, info, **args):
        t0 = dt.utcnow()
        if not root.files:
            res = []

        elif (len(info.field_asts[0].selection_set.selections)==1 and
            info.field_asts[0].selection_set.selections[0].name.value == 'total_count'):
            #OPTIMISE return list of Nones, if total count is the ONLY field selection
            res = FileRelationConnection(edges= [None for x in range(len(root.files))])
            db_metrics.put_duration(__name__, 'resolve_files[total_count]' , dt.utcnow()-t0)

        elif isinstance(root.files[0], dict):
            #new form, files is list of objects
            res = [get_data_manager().file_relation.build_one(file['file_id'], root.id, file['file_role']) for file in root.files]
            db_metrics.put_duration(__name__, 'resolve_files[optimised]' , dt.utcnow()-t0)

        else:
            #old form, files is list of strings
            res = [get_data_manager().file_relation.get_one(_id) for _id in root.files]
            db_metrics.put_duration(__name__, 'resolve_files[legacy]' , dt.utcnow()-t0)

        return res

class ThingConnection(relay.Connection):
    """A Relay connection listing Things"""
    class Meta:
        node = Thing

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)
