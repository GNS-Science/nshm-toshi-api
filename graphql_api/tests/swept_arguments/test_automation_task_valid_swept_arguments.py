"""Automation Task creation/mutation should ensure that arguments
align with and swept args defined in the assocaiated GT (if any)
"""

# from dateutil.tz import tzutc
import datetime
from unittest import mock

import pytest
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id

from graphql_api.schema import root_schema

GENERAL_TASK_OG = {
    "id": "0zHORSE",
    "clazz_name": "GeneralTask",
    "created": "2025-10-30T09:15:00+00:00",
    "title": "GT",
    "description": "Some notes go here",
    "arguments": [
        {"k": "swept", "v": "[" "A" ", " "B" ", " "C" "]"},
    ],
    "metrics": None,
}

CREATE = '''
    mutation ($created: DateTime!, $gt_id: ID!) {
        create_automation_task(input: {
            general_task_id: $gt_id
            task_type: INVERSION
            state: UNDEFINED
            result: UNDEFINED
            created: $created
            duration: 600

            arguments: [
                { k:"max_jump_distance" v: "55.5" }
            ]

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

            ##EXTRA_INPUT##

            }
            )
            {
                task_result {
                id
                general_task_id
                arguments {k v}
                task_type
            }
        }
    }
'''


@pytest.fixture
def graphql_client():
    yield Client(root_schema)


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
def test_create_minimum_fields_happy_case(graphql_client):
    executed = graphql_client.execute(
        CREATE,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), gt_id=to_global_id("GeneralTask", GENERAL_TASK_OG["id"])
        ),
    )
    print(executed)
    assert executed['data']['create_automation_task']['task_result']['id'] == 'QXV0b21hdGlvblRhc2s6MA=='
    assert executed['data']['create_automation_task']['task_result']['task_type'] == 'INVERSION'
    assert from_global_id(executed['data']['create_automation_task']['task_result']['general_task_id']) == (
        "GeneralTask",
        GENERAL_TASK_OG["id"],
    )
