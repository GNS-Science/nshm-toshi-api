"""
For API data management we want a way to iterate all the objects in the store.
"""

import pytest

from graphql_api.data import FileData, TableData, ThingData
from graphql_api.schema import root_schema
from graphql_api.schema.get_datastore_handler import get_datastore_handler, get_datastore_handler_class


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
    """
    NB this test only checks one way, it's possible for a class to be 
    added to the schema without appearing above.
    """

    class_map = {x[0]: x for x in CLASS_MAPPINGS}

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
