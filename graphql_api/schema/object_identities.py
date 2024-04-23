
import graphene
import logging

from graphene import relay, Node
from graphql_relay import from_global_id, to_global_id
from .get_datastore_handler import get_datastore_handler
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

def paginated_object_identities(object_type, **kwargs) -> ObjectIdentitiesConnection:
    '''does the work for the schema resolver'''
    log.info(f'resolve_object_identities args: {kwargs}')

    first = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')     # cursor of last page, or none
    log.debug(f'paginated_object_identities first={first}, after={after}')

    cursor_offset = int(from_global_id(after)[1]) + 1 if after else 0

    # rupture_ids = list(rupture_sections_gdf["Rupture Index"])

    datastore_handler = get_datastore_handler(object_type)
    log.debug(datastore_handler)

    nodes = [ObjectIdentity(**itm) for itm in datastore_handler.get_all(limit=first)]

    # print(gen)
    # assert 0
    # nodes = l[
    #     CompositeRuptureDetail(model_id=model_id, fault_system=fault_system, rupture_index=rid)
    #     for rid in rupture_ids[cursor_offset : cursor_offset + first]
    # ]

    # based on https://gist.github.com/AndrewIngram/b1a6e66ce92d2d0befd2f2f65eb62ca5#file-pagination-py-L152
    edges = [
        ObjectIdentitiesConnection.Edge(
            node=node, cursor=to_global_id("ObjectIdentitiesConnectionCursor", str(cursor_offset + idx))
        )
        for idx, node in enumerate(nodes)
    ]

    # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
    connection_field = relay.ConnectionField.resolve_connection(ObjectIdentitiesConnection, {}, edges)

    has_next = False # TODO total_count > 1 + int(from_global_id(edges[-1].cursor)[1]) if edges else False

    connection_field.page_info = relay.PageInfo(
        end_cursor=edges[-1].cursor
        if edges
        else None,  # graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
        has_next_page=has_next,
    )
    connection_field.edges = edges
    return connection_field