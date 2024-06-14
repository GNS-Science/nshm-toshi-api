from graphql_api.schema import root_schema


def test_iterate_schema_types():
    print(dir(root_schema))
    print(dir(root_schema.graphql_schema))
    for name, _type in root_schema.graphql_schema.type_map.items():
        if hasattr(_type, "interfaces"):
            i_names = [interface.name for interface in _type.interfaces]
            if 'Node' in i_names:
                print(_type.name)
                print(i_names)
    # assert 0
