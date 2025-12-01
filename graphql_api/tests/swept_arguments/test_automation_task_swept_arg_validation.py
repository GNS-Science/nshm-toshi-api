"""Automation Task creation/mutation should ensure that arguments
align with and swept args defined in the assocaiated GT (if any)
"""

# from dateutil.tz import tzutc
import datetime
from unittest.mock import MagicMock

import pytest
from moto import mock_aws

import graphql_api.data.data_manager  # for monkeypatch


@pytest.fixture(autouse=True)
def patch_the_search(monkeypatch):
    monkeypatch.setattr(graphql_api.data.data_manager.dm_instance, '_search_manager', MagicMock())


@mock_aws
class TestGroupATSweptArgValidation:
    """Test new validations behaviour for AT,

    Where any GT swept arguments:

    - must exist
    - must match some member of the corresponding argument_list

    """

    def setup_gt(self, graphql_client, create_gt_mutation):
        # create the GT to be referenced in the AT
        gt1 = graphql_client.execute(
            create_gt_mutation,
            variable_values=dict(
                created=datetime.datetime.now(datetime.UTC),
                argument_lists=[
                    dict(k="swept_arg", v=["A", "B"]),  # this is converted to swept arg
                ],
            ),
        )
        print(gt1)
        return gt1['data']['create_general_task']['general_task']

    @pytest.mark.parametrize(
        "arguments",
        [
            [dict(k="swept_arg", v="A")],
            [dict(k="unswept_arg", v="Q")],
            [dict(k="swept_arg", v="A"), dict(k="unswept_arg", v="Q")],
        ],
    )
    def test_argument_validation_OK(self, graphql_client, create_gt_mutation, create_at_mutation, arguments):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Now attempt to create the AT
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), gt_id=gt['id'], arguments=arguments),
        )
        print(executed)
        at = executed['data']['create_automation_task']['task_result']
        assert arguments == at['arguments']

    @pytest.mark.parametrize(
        "arguments",
        [
            dict(k="swept_arg", v="A"),
            dict(k="unswept_arg", v="Q"),
        ],
    )
    @pytest.mark.skip('WIP')
    def test_argument_validation_FAIL(self, graphql_client, create_gt_mutation, create_at_mutation, arguments):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Now attempt to create the AT
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), gt_id=gt['id'], arguments=arguments),
        )
        print(executed)
        errors = executed.get('errors', [])
        assert len(errors)
