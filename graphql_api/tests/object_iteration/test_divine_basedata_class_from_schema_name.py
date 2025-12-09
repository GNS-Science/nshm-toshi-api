"""
For API data management we want a way to iterate all the objects in the store.

TO do this we at least need to know the object type (is the ModelName).

- all the model typses are dfeind in the graphql schema  (e.g. GeneralTask, File, RuptureSet, OpenquakeHazardSolution)
- let figure out where to go looking based on the class name
"""

import pytest

from graphql_api.data import FileData, TableData, ThingData
from graphql_api.schema import root_schema
from graphql_api.schema.get_datastore_handler import get_datastore_handler, get_datastore_handler_class

# @pytest.mark.parametrize('classname', ['File', 'StrongMotionStation', 'GeneralTask'])
# def test_resolve_clazzname(classname):
#     namespace = globals()
#     clazz = namespace.get(classname)
#     assert clazz._meta.name == classname


# RuptureGenerationTask
# ['Node', 'Thing', 'AutomationTaskInterface']
# SmsFile
# ['Node', 'FileInterface']
# File
# ['Node', 'FileInterface', 'PredecessorsInterface']
# AggregateInversionSolution
# ['Node', 'FileInterface', 'PredecessorsInterface', 'InversionSolutionInterface']
# Table
# ['Node']
# AutomationTask
# ['Node', 'Thing', 'AutomationTaskInterface']
# GeneralTask
# ['Node', 'Thing']
# OpenquakeHazardTask
# ['Node', 'Thing', 'AutomationTaskInterface']
# OpenquakeHazardConfig
# ['Node', 'Thing']
# InversionSolutionNrml
# ['Node', 'FileInterface', 'PredecessorsInterface']
# InversionSolution
# ['Node', 'InversionSolutionInterface', 'FileInterface', 'PredecessorsInterface']
# ScaledInversionSolution
# ['Node', 'FileInterface', 'PredecessorsInterface', 'InversionSolutionInterface']
# TimeDependentInversionSolution
# ['Node', 'FileInterface', 'PredecessorsInterface', 'InversionSolutionInterface']
# OpenquakeHazardSolution
# ['Node', 'Thing', 'PredecessorsInterface']
# StrongMotionStation
# ['Node', 'Thing']
# ObjectIdentity
# ['Node']


CLASS_MAPPINGS = [
    ('File', FileData),
    ('Table', TableData),
    ('StrongMotionStation', ThingData),
    ('GeneralTask', ThingData),
    ('RuptureGenerationTask', ThingData),
    ('SmsFile', FileData),
    ('InversionSolution', FileData),
    ('AggregateInversionSolution', FileData),
    ('TimeDependentInversionSolution', FileData),
    ('ScaledInversionSolution', FileData),
    ('InversionSolutionNrml', FileData),
    ('OpenquakeHazardConfig', ThingData),
    ('OpenquakeHazardSolution', ThingData),
    ('OpenquakeHazardTask', ThingData),
    ('InversionSolution', FileData),
    ('RuptureSet', FileData),
]


def test_class_mappings_are_complete():
    class_map = {x[0]: x for x in CLASS_MAPPINGS}

    # for name, _type in root_schema.graphql_schema.type_map.items():
    #     if name in ["QueryRoot", "PageInfo", "Node", "Thing", "F"]:
    #         continue
    #     if "Connection" in name:
    #         continue
    #     if name[-4:] == "Edge":
    #         continue
    #     if hasattr(_type, "interfaces"):
    #         assert name in class_map.keys()

    for name in class_map.keys():
        assert name in root_schema.graphql_schema.type_map.keys()


@pytest.mark.parametrize('classname, expected_dataclass_instance', CLASS_MAPPINGS)
def test_resolve_clazzname_datastore_type(classname, expected_dataclass_instance):
    handler = get_datastore_handler(classname)
    assert isinstance(handler, expected_dataclass_instance)


@pytest.mark.parametrize('classname, expected_class', CLASS_MAPPINGS)
def test_resolve_clazzname_datastore_class(classname, expected_class):
    clazz = get_datastore_handler_class(classname)
    assert type(clazz) is type(expected_class)
