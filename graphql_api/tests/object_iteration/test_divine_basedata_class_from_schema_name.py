"""
For API data management we want a way to iterate all the objects in the store.

TO do this we at least need to know the object type (is the ModelName).

- all the model typses are dfeind in the graphql schema  (e.g. GeneralTask, File, RuptureSet, OpenquakeHazardSolution)
- let figure out where to go looking based on the class name
"""
import graphene
import pytest

from graphql_api.data import FileData, TableData, ThingData
from graphql_api.schema.get_datastore_handler import get_datastore_handler

# @pytest.mark.parametrize('classname', ['File', 'StrongMotionStation', 'GeneralTask'])
# def test_resolve_clazzname(classname):
#     namespace = globals()
#     clazz = namespace.get(classname)
#     assert clazz._meta.name == classname


@pytest.mark.parametrize(
    'classname, expected_dataclass',
    [
        ('File', FileData),
        ('FileInterface', FileData),
        ('StrongMotionStation', ThingData),
        ('GeneralTask', ThingData),
        ('InversionSolutionNrml', FileData),
        ('OpenquakeHazardSolution', ThingData),
        ('OpenquakeHazardTask', ThingData),
        ('InversionSolution', FileData),
        ('Table', TableData),
    ],
)
def test_resolve_clazzname_datastore_type(classname, expected_dataclass):
    # namespace = globals()
    # clazz = namespace.get(classname)
    # print(clazz)
    # print(type(clazz))
    # assert clazz._meta.name == classname

    # # TODO: move this to an appropriate home
    # def get_handler_via_interface(schema_clazz):
    #     """find the data handler via interace implemented by the schema class

    #     this covers almost all the custom schema types e.g InversionSolutionNrml
    #     """
    #     assert isinstance(schema_clazz, (graphene.ObjectType, graphene.utils.subclass_with_meta.SubclassWithMeta_Meta))
    #     interfaces = [interface._meta.name for interface in schema_clazz._meta.interfaces]
    #     print(interfaces)
    #     for interface in interfaces:
    #         if interface in ['File', 'FileInterface', 'Thing', 'Table']:
    #             return namespace.get(interface).get_object_store_handler()

    # try:
    #     handler = clazz.get_object_store_handler()
    # except AttributeError:
    #     handler = get_handler_via_interface(clazz)

    handler = get_datastore_handler(classname)

    assert isinstance(handler, expected_dataclass)
