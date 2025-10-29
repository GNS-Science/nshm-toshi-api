import logging
from datetime import datetime as dt
from datetime import timezone
from typing import TYPE_CHECKING

import graphene
from graphene import relay

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager
from graphql_api.schema.file_relation import FileRelationConnection

logger = logging.getLogger(__name__)

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)


if TYPE_CHECKING:
    from graphql_api.data import ThingData


class Thing(graphene.Interface):
    """A Thing in the NSHM saga"""

    # class Meta:
    #     interfaces = (relay.Node,)

    created = graphene.DateTime(description="When the thing was created")

    files = relay.ConnectionField(FileRelationConnection, description="Files associated with this object.")
    parents = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection', description="Parents of this thing"
    )

    children = relay.ConnectionField(
        'graphql_api.schema.task_task_relation.TaskTaskRelationConnection', description="Children of this thing"
    )

    def resolve_files(root, info, **args):
        t0 = dt.now(timezone.utc)
        if not root.files:
            res = []

        elif (
            len(info.field_nodes[0].selection_set.selections) == 1
            and info.field_nodes[0].selection_set.selections[0].name.value == 'total_count'
        ):
            # OPTIMISE return list of Nones, if total count is the ONLY field selection
            res = FileRelationConnection(edges=[None for x in range(len(root.files))])
            db_metrics.put_duration(__name__, 'resolve_files[total_count]', dt.now(timezone.utc) - t0)

        elif isinstance(root.files[0], dict):
            # new form, files is list of objects
            res = [
                get_data_manager().file_relation.build_one(file['file_id'], root.id, file['file_role'])
                for file in root.files
            ]
            db_metrics.put_duration(__name__, 'resolve_files[optimised]', dt.now(timezone.utc) - t0)

        else:
            # old form, files is list of strings
            res = [get_data_manager().file_relation.get_one(_id) for _id in root.files]
            db_metrics.put_duration(__name__, 'resolve_files[legacy]', dt.now(timezone.utc) - t0)

        return res

    def resolve_parents(root, info, **args):
        t0 = dt.now(timezone.utc)

        logger.info(f'>> Thing.resolve_parents() ROOT: {root} INFO: {info}')

        if not root.parents:
            res = []
        elif (
            len(info.field_nodes[0].selection_set.selections) == 1
            and info.field_nodes[0].selection_set.selections[0].name.value == 'total_count'
        ):
            from graphql_api.schema.task_task_relation import TaskTaskRelationConnection

            res = TaskTaskRelationConnection(edges=[None for x in range(len(root.parents))])
        elif isinstance(root.parents[0], dict):
            # print(f'#new form, parents is list of objects')
            res = [get_data_manager().thing_relation.build_one(parent['parent_id'], root.id) for parent in root.parents]
            db_metrics.put_duration(__name__, 'resolve_parents[optimised]', dt.now(timezone.utc) - t0)
        else:
            print(f'#old form, parents is list of strings: {root.parents}')
            res = [get_data_manager().thing_relation.get_one(_id) for _id in root.parents]
            db_metrics.put_duration(__name__, 'resolve_parents[legacy]', dt.now(timezone.utc) - t0)

        logger.info(f'>> Thing.resolve_parents() res: {res}')
        return res

    def resolve_children(root, info, **args):
        t0 = dt.now(timezone.utc)
        logger.info(f'>> Thing.resolve_children() ROOT: {root}')
        logger.info(f'>> Thing.resolve_children() INFO: {info}')
        # logger.info(f'>> Thing.resolve_children() : {dir(info.field_nodes[0])}')
        # logger.info(f'>> Thing.resolve_children() : {info.field_nodes[0].name.value}')
        # logger.info(f'>> Thing.resolve_children() : {info.field_nodes[0].selection_set.selections}')

        if not root.children:
            res = []
        elif (
            len(info.field_nodes[0].selection_set.selections) == 1
            and info.field_nodes[0].selection_set.selections[0].name.value == 'total_count'
        ):
            from graphql_api.schema.task_task_relation import TaskTaskRelationConnection

            res = TaskTaskRelationConnection(edges=[None for x in range(len(root.children))])
        elif isinstance(root.children[0], dict):
            # print(f'#new form, children is list of objects')
            res = [get_data_manager().thing_relation.build_one(root.id, child['child_id']) for child in root.children]
            db_metrics.put_duration(__name__, 'resolve_children[optimised]', dt.now(timezone.utc) - t0)
        else:
            # old form, files is list of strings
            res = [get_data_manager().thing_relation.get_one(_id) for _id in root.children]
            db_metrics.put_duration(__name__, 'resolve_children[legacy]', dt.now(timezone.utc) - t0)

        logger.info(f'>> Thing.resolve_children() res: {res}')
        return res

    @staticmethod
    def get_object_store_handler() -> 'ThingData':
        return get_data_manager().thing


class ThingConnection(relay.Connection):
    """A Relay connection listing Things"""

    class Meta:
        node = Thing

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info, *args, **kwargs):
        return len(root.edges)
