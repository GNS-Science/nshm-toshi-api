'''Module showing validation on new RuptureSet mutation operations

These are probably overkill as these are really just testing standard graphql/graphene library behaviours.'''

import datetime
from unittest.mock import MagicMock

import pytest
from graphql_relay import from_global_id
from moto import mock_aws

import graphql_api.data.data_manager  # for monkeypatch
from graphql_api.dynamodb.models import migrate


@pytest.fixture(autouse=True)
def patch_the_search(monkeypatch):
    monkeypatch.setattr(graphql_api.data.data_manager.dm_instance, '_search_manager', MagicMock())


@mock_aws()
def test_create_rupture_generation_task_happy_case(rupture_generation_task):
    print(rupture_generation_task)
    assert from_global_id(rupture_generation_task['id']) == ("AutomationTask", "100001")


def assert_string_in_messages(expected: str, messages):
    """test helper to parse and validate error messages"""
    found = False
    for message in messages:
        if expected in message:
            found = True
            break
    assert found


@mock_aws()
def test_create_rupture_set_with_missing_file_attributes_fails(
    graphql_client, rupture_generation_task, create_rupture_set_mutation
):
    query = '''
            mutation {
                create_rupture_set(
                    input: {
                    created: "2022-03-03T00:17:52.352274+00:00"
                    }
              ) {
              rupture_set {id}
              }
              }
            '''
    executed = gt1 = graphql_client.execute(query)

    print(executed)
    assert executed['data'] == None
    assert len(executed['errors'])
    messages = [x['message'] for x in executed['errors']]
    assert_string_in_messages("file_name", messages)
    assert_string_in_messages("file_size", messages)
    assert_string_in_messages("md5_digest", messages)


@pytest.mark.parametrize(
    "created, valid_created",
    [
        (datetime.datetime.now(datetime.UTC), True),
        ("", False),
        (None, False),
        ("can't parse this as a date", False),
        (1001, False),
    ],
)
@mock_aws()
def test_create_rupture_set_valid_created(
    created, valid_created, graphql_client, rupture_generation_task, create_rupture_set_mutation
):

    executed = graphql_client.execute(
        create_rupture_set_mutation,
        variable_values=dict(
            created=created,
            md5_digest="digest",
            file_name="file_name",
            file_size=1000,
            produced_by=rupture_generation_task['id'],
            metrics=[{"k": "some_metric", "v": "20"}],
            arguments=[dict(k="random_arg", v="A")],
            fault_models=["A", "B"],
        ),
    )
    print(executed)

    if valid_created:
        node = executed['data']['create_rupture_set']['rupture_set']
        print(node)
        assert from_global_id(node['id'])[0] == "RuptureSet"
        assert node['file_name'] == "file_name"
    else:
        assert executed['data'] == None
        assert len(executed['errors'])
        messages = [x['message'] for x in executed['errors']]
        assert_string_in_messages("created", messages)


@pytest.mark.parametrize(
    "fault_models, valid_fault_models",
    [
        (["ModelA", "ModelB"], True),
        (None, False),
        (1001, False),
    ],
)
@mock_aws()
def test_create_rupture_set_valid_fault_models(
    fault_models, valid_fault_models, graphql_client, rupture_generation_task, create_rupture_set_mutation
):

    executed = graphql_client.execute(
        create_rupture_set_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC),
            md5_digest="digest",
            file_name="file_name",
            file_size=1000,
            produced_by=rupture_generation_task['id'],
            metrics=[{"k": "some_metric", "v": "20"}],
            arguments=[dict(k="random_arg", v="A")],
            fault_models=fault_models,
        ),
    )
    print(executed)

    if valid_fault_models:
        node = executed['data']['create_rupture_set']['rupture_set']
        print(node)
        assert from_global_id(node['id'])[0] == "RuptureSet"
        assert node['file_name'] == "file_name"
    else:
        assert executed['data'] == None
        assert len(executed['errors'])
        messages = [x['message'] for x in executed['errors']]
        assert_string_in_messages("fault_models", messages)
