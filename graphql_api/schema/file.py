"""
The NSHM data file graphql schema.
"""

from datetime import datetime as dt

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.data.file_relation_data import ensure_decompressed
from graphql_api.schema.custom.common import KeyValuePair, KeyValuePairInput, PredecessorsInterface
from graphql_api.schema.custom.scalars import BigInt

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


class FileInterface(graphene.Interface):
    """A File in the NSHM saga"""

    class Meta:
        interfaces = relay.Node

    # TODO consider if this field ought to be enforced here, instead of in subclasses
    # created = graphene.DateTime(description="When the file was created")
    file_name = graphene.String(description="The name of the file")
    md5_digest = graphene.String(description='The base64-encoded md5 digest of the file')
    file_size = BigInt(description="The size of the file in bytes")
    file_url = graphene.String(description="A pre-signed URL to download the file from s3")
    post_url = graphene.String(description="A pre-signed URL to post the data to s3")

    meta = graphene.List(
        KeyValuePair, required=False, description="additional file meta data, as a list of Key Value pairs."
    )

    relations = relay.ConnectionField(
        'graphql_api.schema.thing.FileRelationConnection', description="things related to this data file"
    )

    def resolve_file_url(self, info, **args):
        return get_data_manager().file.get_presigned_url(self.id)

    def resolve_relations(root, info, **args):
        # Transform the instance thing_ids into real instances
        t0 = dt.utcnow()
        root_relations = ensure_decompressed(root.relations)

        root_relations = root_relations or []

        if (
            len(info.field_asts[0].selection_set.selections) == 1
            and info.field_asts[0].selection_set.selections[0].name.value == 'total_count'
        ):
            from graphql_api.schema.file_relation import FileRelationConnection

            res = FileRelationConnection(edges=[None for x in range(len(root_relations))])
            db_metrics.put_duration(__name__, 'resolve_relations[total_count]', dt.utcnow() - t0)

        elif isinstance(root_relations[0], dict):
            # new form, files is list of objects
            res = [
                get_data_manager().file_relation.build_one(root.id, relation['id'], relation['role'])
                for relation in root_relations
            ]
            db_metrics.put_duration(__name__, 'resolve_relations[optimised]', dt.utcnow() - t0)

        else:
            # old form, files is list of strings
            res = [get_data_manager().file_relation.get_one(_id) for _id in root_relations]
            db_metrics.put_duration(__name__, 'resolve_relations[legacy]', dt.utcnow() - t0)

        return res

    @staticmethod
    def get_object_store_handler() -> "FileData":
        return get_data_manager().file


class File(graphene.ObjectType):
    """A data file"""

    class Meta:
        """standard graphene meta class"""

        interfaces = (relay.Node, FileInterface, PredecessorsInterface)

    @classmethod
    def get_node(cls, info, _id):
        # t0 = dt.utcnow()
        node = get_data_manager().file.get_one(_id)
        # db_metrics.put_duration(__name__, 'CreateFile.mutate' , dt.utcnow()-t0)
        return node

    @staticmethod
    def get_object_store_handler() -> "FileData":
        return get_data_manager().file


class FileConnection(relay.Connection):
    """A Relay connection for Files"""

    class Meta:
        node = File

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)


class CreateFile(graphene.Mutation):
    class Arguments:
        file_name = graphene.String()
        md5_digest = graphene.String("The base64-encoded md5 digest of the file")
        file_size = BigInt()
        meta = graphene.List(
            KeyValuePairInput, required=False, description="additional file meta data, as a list of Key Value pairs."
        )

        predecessors = graphene.List(
            'graphql_api.schema.custom.predecessor.PredecessorInput', required=False, description="list of predecessors"
        )

    ok = graphene.Boolean()
    file_result = graphene.Field(File)

    def mutate(self, info, **kwargs):
        t0 = dt.utcnow()
        file_result = get_data_manager().file.create('File', **kwargs)
        db_metrics.put_duration(__name__, 'CreateFile.mutate', dt.utcnow() - t0)
        return CreateFile(ok=True, file_result=file_result)
