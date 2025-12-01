"""Automation Task creation/mutation should ensure that arguments
align with and swept args defined in the assocaiated GT (if any)
"""

# from dateutil.tz import tzutc
import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from graphql_relay import from_global_id, to_global_id
from moto import mock_aws

import graphql_api.data.data_manager  # for monkeypatch
from graphql_api.dynamodb.models import migrate


@pytest.fixture(autouse=True)
def patch_the_search(monkeypatch):
    monkeypatch.setattr(graphql_api.data.data_manager.dm_instance, '_search_manager', MagicMock())


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
def test_create_minimum_fields_happy_case(graphql_client, create_at_mutation):
    executed = graphql_client.execute(
        create_at_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC),
            gt_id=to_global_id("GeneralTask", "555"),
            arguments=dict(k="max_jump_distance", v="55.5"),
        ),
    )
    print(executed)
    assert executed['data']['create_automation_task']['task_result']['id'] == 'QXV0b21hdGlvblRhc2s6MA=='
    assert executed['data']['create_automation_task']['task_result']['task_type'] == 'INVERSION'
    assert from_global_id(executed['data']['create_automation_task']['task_result']['general_task_id']) == (
        "GeneralTask",
        "555",
    )


@mock_aws()
def test_fullstack_create_minimum_fields_happy_case(graphql_client, create_gt_mutation, create_at_mutation):
    """This is the fullstack alternative of the prior example.

    Notes:

     - the mocked datastore setup and migration() is handled in the graphql_client fixture
     - elastic search is mocked out with autouse/monkeypatch in conftest.py
    """

    # create the GT to be referenced in the AT
    gt1 = graphql_client.execute(
        create_gt_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), argument_lists=[dict(k="swept_arg", v=["A", "B"])]
        ),
    )
    print(gt1)
    gt_id = gt1['data']['create_general_task']['general_task']['id']

    # Now create the AT
    executed = graphql_client.execute(
        create_at_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), gt_id=gt_id, arguments=dict(k="max_jump_distance", v="55.5")
        ),
    )
    print(executed)
    assert executed['data']['create_automation_task']['task_result']['id'] == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
    assert executed['data']['create_automation_task']['task_result']['task_type'] == 'INVERSION'
    assert executed['data']['create_automation_task']['task_result']['general_task_id'] == gt_id


@mock_aws()
def test_swept_arguments_are_implied_from_GT_argument_lists(graphql_client, create_gt_mutation, create_at_mutation):
    """This shows current behaviour where swept_arguments returns a list of
    keys for variable that match swept args rules i.e. len(v)==1

    """
    # create the GT to be referenced in the AT
    gt1 = graphql_client.execute(
        create_gt_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC),
            argument_lists=[
                dict(k="swept_arg", v=["A", "B"]),  # this is converted to swept arg
                dict(k="unswept_arg", v=["A"]),  # this is not converted
                dict(k="empty_arg", v=[]),  # this is not converted
            ],
        ),
    )
    print(gt1)
    general_task = gt1['data']['create_general_task']['general_task']
    gt_id = general_task['id']

    # argument_lists
    assert dict(k="unswept_arg", v=["A"]) in general_task['argument_lists']
    assert dict(k="swept_arg", v=["A", "B"]) in general_task['argument_lists']
    assert dict(k="empty_arg", v=[]) in general_task['argument_lists']

    # swept_arguments implied
    assert "empty_arg" not in general_task['swept_arguments']
    assert "unswept_arg" not in general_task['swept_arguments']
    assert "swept_arg" in general_task['swept_arguments']
