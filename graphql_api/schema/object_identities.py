import logging

import graphene
from graphene import Node, relay
from graphql_relay import from_global_id, to_global_id

from graphql_api.data import get_data_manager

from .get_datastore_handler import get_datastore_handler, get_datastore_handler_names, get_datastore_handlers

log = logging.getLogger(__name__)


class ObjectIdentity(graphene.ObjectType):
    class Meta:
        interfaces = (Node,)

    object_type = graphene.String()
    object_id = graphene.String()
    clazz_name = graphene.String()
    node_id = graphene.ID()


class ObjectIdentitiesConnection(relay.Connection):
    class Meta:
        node = ObjectIdentity


def iterate_dynamodb_nodes(object_type, **kwargs):
    """loop over all the object_types"""
    # for object_type in get_datastore_handler_names():
    limit = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none
    datastore_handler = get_datastore_handler(object_type)
    cursor_offset = from_global_id(after)[1] if after else "-1"
    log.info(f"datastore_handler: {datastore_handler}")
    for itm in datastore_handler.get_all(object_type, limit=limit, after=cursor_offset):
        yield ObjectIdentity(
            object_type=itm.object_type, object_id=itm.object_id, node_id=to_global_id(itm.object_type, itm.object_id)
        )


def iterate_legacy_s3_nodes(store_type, **kwargs):
    datastore = get_data_manager().datastores[store_type]
    limit = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none
    after = from_global_id(after)[1] if after else ""
    for itm in datastore.get_all_s3_paginated(limit, after):
        yield ObjectIdentity(
            object_type=itm.object_type, object_id=itm.object_id, node_id=to_global_id(itm.object_type, itm.object_id)
        )


def paginated_object_identities(node_iterable, **kwargs) -> ObjectIdentitiesConnection:
    '''does the work for the schema resolver'''
    log.info(f'resolve_object_identities args: {kwargs}')

    first = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none

    cursor_offset = from_global_id(after)[1] if after else "-1"
    log.info(f'paginated_object_identities first={first}, after={after} cursor_offset: {cursor_offset}')

    # based on https://gist.github.com/AndrewIngram/b1a6e66ce92d2d0befd2f2f65eb62ca5#file-pagination-py-L152
    edges = [
        ObjectIdentitiesConnection.Edge(
            node=node, cursor=to_global_id("ObjectIdentitiesConnectionCursor", node.object_id)
        )
        for node in node_iterable  # enumerate(dynamodb_nodes(limit=first, after=cursor_offset))
    ]

    # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
    connection_field = relay.ConnectionField.resolve_connection(ObjectIdentitiesConnection, {}, edges)

    has_next = False if len(edges) < first else True

    connection_field.page_info = relay.PageInfo(
        end_cursor=(
            edges[-1].cursor if edges else None
        ),  # graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
        has_next_page=has_next,
    )
    connection_field.edges = edges
    return connection_field
