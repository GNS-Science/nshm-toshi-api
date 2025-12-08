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
    assert from_global_id(rupture_generation_task['id']) == ("RuptureGenerationTask", "100001")


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
        ),
    )
    print(executed)

    rupture_set = executed['data']['create_rupture_set']['rupture_set']
    assert from_global_id(rupture_set['id']) == ("RuptureSet", "100000")
    assert rupture_set["produced_by"]['__typename'] == "RuptureGenerationTask"
