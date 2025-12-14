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


@mock_aws()
def test_create_rupture_set_happy_case(graphql_client, rupture_generation_task, create_rupture_set_mutation):

    # prepare the geenration task
    print(rupture_generation_task)

    # Now create the Rupture Generation task
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
            fault_models=["ModelA", "ModelB"],
        ),
    )
    print(executed)

    rupture_set = executed['data']['create_rupture_set']['rupture_set']
    assert from_global_id(rupture_set['id']) == ("RuptureSet", "100000")
    assert rupture_set["produced_by"]['__typename'] == "AutomationTask"
    assert rupture_set["fault_models"] == ["ModelA", "ModelB"]
    assert rupture_set["post_url"] is not None


@pytest.fixture
def create_rupture_set(graphql_client, rupture_generation_task, create_rupture_set_mutation):

    # prepare the generation task
    print(rupture_generation_task)

    # Now create the Rupture Generation task
    executed = graphql_client.execute(
        create_rupture_set_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC),
            md5_digest="digest",
            file_name="file_name",
            file_size=1000,
            produced_by=rupture_generation_task['id'],
            metrics=[{"k": "some_shelley_creation", "v": "20"}],
            meta=[dict(k="random_meta", v="A")],
            fault_models=["ModelA", "ModelB"],
        ),
    )
    yield executed['data']['create_rupture_set']['rupture_set']


@mock_aws()
def test_rupture_set_round_trip_happy_case(graphql_client, create_rupture_set):

    VERIFY_RUPT_SET = '''
        query get_node($node_id: ID!){
          node(id: $node_id) {
            __typename
            ... on RuptureSet {
                id
                created
                file_name
                md5_digest
                file_size
                produced_by { id, __typename }
                meta { k v}
                metrics { k v}
            }
          }
        }
        '''
    # query the API for our fresh rupture set using `RuptureSet` ...
    result = graphql_client.execute(VERIFY_RUPT_SET, variable_values=dict(node_id=create_rupture_set['id']))
    print(result)

    node = result['data']['node']
    assert from_global_id(node['id'])[0] == "RuptureSet"
    assert node["__typename"] == "RuptureSet"
    assert node["produced_by"]['__typename'] == "AutomationTask"
    assert node["meta"][0]['k'] == "random_meta"
    assert node["metrics"][0]['k'] == "some_shelley_creation"


@mock_aws()
def test_rupture_set_round_trip_happy_case_as_file_interface(graphql_client, create_rupture_set):

    VERIFY_FILE_INTERFACE = '''
        query get_node($node_id: ID!){
          node(id: $node_id) {
            __typename
            ... on Node { id }
            ... on FileInterface {
                file_name
                md5_digest
                file_size             
            }
          }
        }
        '''
    # query the API for our fresh rupture set using (`Node`, `FileInterface`) ...
    result = graphql_client.execute(VERIFY_FILE_INTERFACE, variable_values=dict(node_id=create_rupture_set['id']))
    print(result)

    node = result['data']['node']
    assert node["__typename"] == "RuptureSet"
    assert from_global_id(node['id'])[0] == "RuptureSet"
    assert node['file_name'] == "file_name"
