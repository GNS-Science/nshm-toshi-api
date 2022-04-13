from graphql_relay import from_global_id
from importlib import import_module
from datetime import datetime as dt

import logging
from graphql_api.data import get_data_manager
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)
logger = logging.getLogger(__name__)

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

    logger.debug(f"resolve_node() resolving for type {_type}, id: {nid}, id_field: {id_field}, dm_type: {dm_type}")

    if len(info.field_asts[0].selection_set.selections)==1 and \
        (info.field_asts[0].selection_set.selections[0].name.value == 'id'):

        #create an instance with just the id attribute set
        clazz = getattr(import_module('graphql_api.schema'), _type)
        res =  clazz(id=nid)
    else:
        res = getattr(get_data_manager(), dm_type).get_one(nid)

    db_metrics.put_duration(__name__, 'resolve_node' , dt.utcnow()-t0)
    return res
