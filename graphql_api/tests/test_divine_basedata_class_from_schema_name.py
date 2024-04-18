"""
For API data management we want a way to iterate all the objects in the store.

TO do this we at least need to know the object type (is the ModelName).

- all the model typses are dfeind in the graphql schema  (e.g. GeneralTask, File, RuptureSet, OpenquakeHazardSolution)
- let figure out where to go looking based on the class name
"""
import pytest
from graphql_api.schema import File, Table, Thing
from graphql_api.schema.file import FileInterface
from graphql_api.schema.custom import InversionSolution, StrongMotionStation, GeneralTask, OpenquakeHazardSolution
from graphql_api.data import ThingData, FileData, TableData

@pytest.mark.parametrize(
    'classname', ['File', 'StrongMotionStation', 'GeneralTask']
)
def test_resolve_clazzname(classname):
	namespace= globals()
	clazz = namespace.get(classname)
	print(clazz)
	print(type(clazz))
	assert clazz._meta.name == classname


@pytest.mark.parametrize(
	'classname, expected_dataclass',
 	[
 		('File', FileData),
 		('FileInterface', FileData),
 	 	('StrongMotionStation', ThingData),
 	 	('GeneralTask', ThingData),
 	 	('OpenquakeHazardSolution', ThingData),
		('InversionSolution', FileData),
 	 	('Table', TableData)
 	]
)
def test_resolve_clazzname_datastore_type(classname, expected_dataclass):
	namespace= globals()
	clazz = namespace.get(classname)
	print(clazz)
	print(type(clazz))
	assert clazz._meta.name == classname

	def get_handler_via_interface(clazz):
		interfaces = [interface._meta.name for interface in clazz._meta.interfaces]
		print(interfaces)
		for interface in interfaces:
			if interface in ['File', 'FileInterface', 'Thing', 'Table']:
				return namespace.get(interface).get_object_store_handler()
	try:
		handler = clazz.get_object_store_handler()
	except AttributeError:
		 handler = get_handler_via_interface(clazz)

	assert isinstance(handler, expected_dataclass)
