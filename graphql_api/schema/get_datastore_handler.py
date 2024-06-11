from collections import namedtuple
from typing import Union

import graphene

## imports for class resolution
from graphql_api.data import FileData, TableData, ThingData

from .custom import (
    AggregateInversionSolution,
    AutomationTask,
    GeneralTask,
    InversionSolution,
    InversionSolutionNrml,
    OpenquakeHazardConfig,
    OpenquakeHazardSolution,
    OpenquakeHazardTask,
    RuptureGenerationTask,
    ScaledInversionSolution,
    SmsFile,
    StrongMotionStation,
    TimeDependentInversionSolution,
)
from .file import File, FileInterface  # noqa: F401
from .table import Table
from .thing import Thing

SchemaObjectStorageHandler = namedtuple("SchemaObjectStorageType", "schema_class, handler_class")

SCHEMA_STORAGE_HANDLERS = dict(
    AutomationTask=SchemaObjectStorageHandler(AutomationTask, ThingData),
    File=SchemaObjectStorageHandler(File, FileData),
    # SchemaObjectStorageHandler(FileInterface, FileData),
    Table=SchemaObjectStorageHandler(Table, TableData),
    SmsFile=SchemaObjectStorageHandler(SmsFile, FileData),
    StrongMotionStation=SchemaObjectStorageHandler(StrongMotionStation, ThingData),
    GeneralTask=SchemaObjectStorageHandler(GeneralTask, ThingData),
    RuptureGenerationTask=SchemaObjectStorageHandler(RuptureGenerationTask, ThingData),
    AggregateInversionSolution=SchemaObjectStorageHandler(AggregateInversionSolution, FileData),
    InversionSolution=SchemaObjectStorageHandler(InversionSolution, FileData),
    ScaledInversionSolution=SchemaObjectStorageHandler(ScaledInversionSolution, FileData),
    TimeDependentInversionSolution=SchemaObjectStorageHandler(TimeDependentInversionSolution, FileData),
    InversionSolutionNrml=SchemaObjectStorageHandler(InversionSolutionNrml, FileData),
    OpenquakeHazardConfig=SchemaObjectStorageHandler(OpenquakeHazardConfig, ThingData),
    OpenquakeHazardSolution=SchemaObjectStorageHandler(OpenquakeHazardSolution, ThingData),
    OpenquakeHazardTask=SchemaObjectStorageHandler(OpenquakeHazardTask, ThingData),
)


def get_handler_names():
    result = set()
    for handler in SCHEMA_STORAGE_HANDLERS.values():
        result.add(handler.handler_class)
    return list(result)


def get_datastore_handler_names():
    return list(SCHEMA_STORAGE_HANDLERS.keys())


def get_datastore_handlers():
    return list(SCHEMA_STORAGE_HANDLERS.values())


def get_datastore_handler_class(classname: str) -> Union[File, Table, Thing]:
    return SCHEMA_STORAGE_HANDLERS[classname].handler_class


def get_datastore_handler(classname: str) -> Union[File, Table, Thing]:
    namespace = globals()
    clazz = namespace.get(classname)
    assert clazz._meta.name == classname

    def get_handler_via_interface(schema_clazz):
        """find the data handler via interace implemented by the schema class"""
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
