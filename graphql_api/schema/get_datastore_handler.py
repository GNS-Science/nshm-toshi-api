import graphene

## imports for class resolution
# from graphql_api.data import FileData, TableData, ThingData
from .table import Table
from .thing import Thing
from .file import FileInterface, File

from .custom import (
    GeneralTask,
    InversionSolution,
    InversionSolutionNrml,
    OpenquakeHazardSolution,
    OpenquakeHazardTask,
    StrongMotionStation,
)

def get_datastore_handler(classname):
    namespace = globals()
    clazz = namespace.get(classname)
    # print(clazz)
    # print(type(clazz))
    # assert clazz._meta.name == classname
    # TODO: move this to an appropriate home

    def get_handler_via_interface(schema_clazz):
        """find the data handler via interace implemented by the schema class

        this covers almost all the custom schema types e.g InversionSolutionNrml
        """
        assert isinstance(schema_clazz, (graphene.ObjectType, graphene.utils.subclass_with_meta.SubclassWithMeta_Meta))
        interfaces = [interface._meta.name for interface in schema_clazz._meta.interfaces]
        print(interfaces)
        for interface in interfaces:
            if interface in ['File', 'FileInterface', 'Thing', 'Table']:
                return namespace.get(interface).get_object_store_handler()
    try:
        handler = clazz.get_object_store_handler()
    except AttributeError:
        handler = get_handler_via_interface(clazz)
    return handler
