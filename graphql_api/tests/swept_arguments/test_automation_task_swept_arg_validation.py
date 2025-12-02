"""AutomationTask (AT) creation/mutation should validate arguments
defined in the associated GeneralTask (GT).
"""

import datetime
from unittest.mock import MagicMock

import pytest
from graphql_relay import to_global_id
from moto import mock_aws

import graphql_api.data.data_manager  # for monkeypatching the search manager


@pytest.fixture(autouse=True)
def mock_the_global_search_manager(monkeypatch):
    """We don't want to test interactions with the search service here."""
    monkeypatch.setattr(graphql_api.data.data_manager.dm_instance, '_search_manager', MagicMock())


@mock_aws
class TestGroup:
    """Test new validations behaviour for AT,

    Where :

    - any GT swept arguments must exist in the AT, and
    - the AT argument value must match a value in the corresponding GT argument_lists
    """

    def setup_gt(self, graphql_client, create_gt_mutation):
        # create the GT to be referenced in the AT tests
        gt1 = graphql_client.execute(
            create_gt_mutation,
            variable_values=dict(
                created=datetime.datetime.now(datetime.UTC),
                argument_lists=[
                    dict(k="swept_arg", v=["A", "B"]),  # a swept arg
                    dict(k="unswept_arg", v=["BOOM"]),  # a non-swept arg
                ],
            ),
        )
        print(gt1)
        return gt1['data']['create_general_task']['general_task']

    @pytest.mark.parametrize(
        "arguments, message",
        [
            ([dict(k="swept_arg", v="A")], "1 swept"),
            ([dict(k="swept_arg", v="A"), dict(k="unswept_arg", v="Q")], "1 swept, 1 unswept"),
        ],
    )
    def test_argument_validation_OK(self, graphql_client, create_gt_mutation, create_at_mutation, arguments, message):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Now attempt to create the AT
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), gt_id=gt['id'], arguments=arguments),
        )
        print(executed)

        # A valid AT is returned, as the validations succeeded
        at = executed['data']['create_automation_task']['task_result']
        assert arguments == at['arguments']

    @pytest.mark.parametrize(
        "arguments, message",
        [
            ([dict(k="unswept_arg", v="Q")], "missing swept_argument"),
            ([dict(k="swept_arg", v="")], "empty swept_argument"),
            ([dict(k="swept_arg", v="NO")], "bad swept_argument value"),
        ],
    )
    def test_argument_skip_validation_with_no_gt_OK(
        self, graphql_client, create_gt_mutation, create_at_mutation, arguments, message
    ):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Create the AT, without a GeneralTask id
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), arguments=arguments),
        )
        print(executed)

        # A valid AT is returned, as per pre-validation API behaviour
        at = executed['data']['create_automation_task']['task_result']
        assert arguments == at['arguments']

    @pytest.mark.parametrize(
        "arguments, message",
        [
            (
                [dict(k="unswept_arg", v="Q")],
                "swept_arg from GeneralTask.swept_arguments was not found in new AutomationTask.",
            ),
            (
                [dict(k="swept_arg", v="")],
                f"not a member of GeneralTask.swept_arguments values",
            ),
            (
                [dict(k="swept_arg", v="NO")],
                f"not a member of GeneralTask.swept_arguments values",
            ),
        ],
    )
    def test_argument_validation_expected_to_FAIL(
        self, graphql_client, create_gt_mutation, create_at_mutation, arguments, message
    ):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Now attempt to create the AT
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), gt_id=gt['id'], arguments=arguments),
        )
        print(executed)

        # A useful error message is returned
        errors = executed.get('errors', [])
        assert len(errors)
        assert message in errors[0]['message']

        # No new Automation Task was created
        assert executed['data']['create_automation_task'] is None

    @pytest.mark.parametrize(
        "gt_id, message",
        [
            (
                to_global_id("GeneralTask", "99"),
                "was not found",
            ),
            (
                to_global_id("FasterTurtle", "1"),
                f"is not a `GeneralTask`",
            ),
        ],
    )
    def test_invalid_gt_id_expected_to_FAIL(
        self, graphql_client, create_gt_mutation, create_at_mutation, gt_id, message
    ):
        gt = self.setup_gt(graphql_client, create_gt_mutation)

        # Now attempt to create the AT
        executed = graphql_client.execute(
            create_at_mutation,
            variable_values=dict(created=datetime.datetime.now(datetime.UTC), gt_id=gt_id, arguments=[]),
        )
        print(executed)

        # A useful error message is returned
        errors = executed.get('errors', [])
        assert len(errors)
        assert message in errors[0]['message']

        # No new Automation Task was created
        assert executed['data']['create_automation_task'] is None
