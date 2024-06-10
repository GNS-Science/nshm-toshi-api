import copy
import logging
from datetime import datetime as dt
from importlib import import_module

import graphql.language.ast
from graphql_relay import from_global_id

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data import get_data_manager

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)
log = logging.getLogger(__name__)


def resolve_node(root, info, id_field, dm_type):
    """
    Optimisation function, looks at the query and avoids a fetch if
    we only want to resolve the id field.
    """
    t0 = dt.utcnow()
    assert dm_type in ["table", "thing", 'file']

    node_id = getattr(root, id_field)
    if not node_id:
        return

    _type, nid = from_global_id(node_id)

    log.debug(f"resolve_node() resolving for type {_type}, id: {nid}, id_field: {id_field}, dm_type: {dm_type}")

    def typename_field(selections):
        for selection in selections:
            log.debug(f'selection {type(selection)}')
            if isinstance(selection, graphql.language.ast.InlineFragment):
                continue
            if selection.name.value == '__typename':
                return selection

    selections = copy.copy(info.field_asts[0].selection_set.selections)
    log.debug(f"resolve_node selections A {selections}")
    type_name_field = typename_field(selections)
    if type_name_field:
        selections.remove(type_name_field)

    log.debug(f"resolve_node selections B {selections}")
    if len(selections) == 1 and getattr(selections[0], "type_condition", None):
        """We have a sub-selection InlineFragment (e.g `... on Node { ...`, so drill in one more level"""
        selections = copy.copy(selections[0].selection_set.selections)

    log.debug(f"resolve_node selections C {selections}")

    if len(selections) == 1 and (selections[0].name.value == 'id'):
        # create an instance with just the id attribute set
        log.debug(f"resolve_node no fetch needed")
        clazz = getattr(import_module('graphql_api.schema'), _type)
        res = clazz(id=nid)
    else:

        res = getattr(get_data_manager(), dm_type).get_one(nid)

    log.debug(f"resolve_node() returning  {res}")

    db_metrics.put_duration(__name__, 'resolve_node', dt.utcnow() - t0)
    return res
