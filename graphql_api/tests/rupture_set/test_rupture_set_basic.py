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


@pytest.fixture()
def rupture_generation_task(graphql_client, create_gt_mutation, create_rs_mutation):

    # create the GT to be referenced in the AT
    gt1 = graphql_client.execute(
        create_gt_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), argument_lists=[dict(k="swept_arg", v=["A", "B"])]
        ),
    )
    print(gt1)
    gt_id = gt1['data']['create_general_task']['general_task']['id']

    # Now create the Rupture Generation task
    executed = graphql_client.execute(
        create_rs_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), gt_id=gt_id, arguments=dict(k="swept_arg", v="A")
        ),
    )
    task_result = executed['data']['create_rupture_generation_task']['task_result']
    yield task_result


@mock_aws()
def test_create_rupture_generation_task_happy_case(rupture_generation_task):
    assert from_global_id(rupture_generation_task['id']) == ("RuptureGenerationTask", "100001")
    print(rupture_generation_task)


@pytest.fixture()
def create_rupture_set_mutation():
    yield """
        mutation (
            $md5_digest: String!, 
            $file_name: String!, 
            $file_size: BigInt!, 
            $produced_by: ID!
            $arguments: [KeyValuePairInput],
            $metrics: [KeyValuePairInput],
            $created: DateTime!
        ) {
              create_rupture_set(
                input: {
                  md5_digest: $md5_digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by: $produced_by
                  arguments: $arguments
                  metrics: $metrics
                  created: $created
                  }
              ) {
              rupture_set { 
                id
                file_name
                file_size
                md5_digest
                created
                produced_by { id __typename, general_task_id}
                arguments { k v }
                metrics { k v }
                }
              }
            }
    """


@mock_aws()
def test_create_rupture_set_happy_case(graphql_client, rupture_generation_task, create_rupture_set_mutation):

    print(rupture_generation_task)
    print()
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


# @mock_aws()
# def test_swept_arguments_are_implied_from_GT_argument_lists(graphql_client, create_gt_mutation, create_at_mutation):
#     """This shows current behaviour where swept_arguments returns a list of
#     keys for variable that match swept args rules i.e. len(v)==1

#     """
#     # create the GT to be referenced in the AT
#     gt1 = graphql_client.execute(
#         create_gt_mutation,
#         variable_values=dict(
#             created=datetime.datetime.now(datetime.UTC),
#             argument_lists=[
#                 dict(k="swept_arg", v=["A", "B"]),  # this is converted to swept arg
#                 dict(k="unswept_arg", v=["A"]),  # this is not converted
#                 dict(k="empty_arg", v=[]),  # this is not converted
#             ],
#         ),
#     )
#     print(gt1)
#     general_task = gt1['data']['create_general_task']['general_task']
#     gt_id = general_task['id']

#     # argument_lists
#     assert dict(k="unswept_arg", v=["A"]) in general_task['argument_lists']
#     assert dict(k="swept_arg", v=["A", "B"]) in general_task['argument_lists']
#     assert dict(k="empty_arg", v=[]) in general_task['argument_lists']

#     # swept_arguments implied
#     assert "empty_arg" not in general_task['swept_arguments']
#     assert "unswept_arg" not in general_task['swept_arguments']
#     assert "swept_arg" in general_task['swept_arguments']
