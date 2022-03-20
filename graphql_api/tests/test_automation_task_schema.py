
"""
Test API function for opensha Rupture Generation

Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data

from graphql_api.schema import root_schema, AutomationTask

import graphql_api.data # for mocking


# class IncrId():
#     next_id = -1

#     def get_next_id(self, *args):
#         self.next_id +=1
#         return self.next_id

READ_MOCK = lambda _self, id: dict(
    id = "0",
    clazz_name = "AutomationTask",
    task_type = "INVERSION",
    model_type = "SUBDUCTION",
    created = "2021-06-11T02:37:26.009506+00:00",
    meta = [{ "k":"some_metric", "v": "55.5" }],
    )


CREATE = '''
    mutation ($created: DateTime!) {
        create_automation_task(input: {
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
                task_type
                created
                duration
                arguments {k v}
            }
        }
    }
'''


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
class TestCreateAutomationTask(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE,
            variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['create_automation_task']['task_result']['id'] == 'QXV0b21hdGlvblRhc2s6MA=='
        assert executed['data']['create_automation_task']['task_result']['task_type'] == 'INVERSION'

    def test_date_must_include_timezone(self):
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(CREATE, variable_values=dict(created=startdate))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                create_automation_task(input: {
                    created: "September 5th, 1999"
                    })
                    {
                        task_result {
                        id
                    }
                }
            }
        '''
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(qry)
        print(executed)
        assert 'Expected type "DateTime", found "September 5th, 1999"' in executed['errors'][0]['message']

    def test_create_with_metrics(self):
        insert = '''
            metrics: [
                {k:"rupture_count" v:"206776"}
            ]
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)
        print(qry)
        executed = self.client.execute(qry, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['create_automation_task']\
                        ['task_result']['id'] == 'QXV0b21hdGlvblRhc2s6MA=='


TASKZERO = lambda _self, _id: {
    "id": "0",
    "clazz_name": "RuptureGenerationTask",
    "created": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "arguments": [
            { "k":"max_jump_distance", "v": "55.5" },
            { "k":"max_sub_section_length", "v": "2" },
            { "k":"max_cumulative_azimuth", "v": "590" },
            { "k":"min_sub_sections_per_parent", "v": "2" },
            { "k":"permutation_strategy", "v": "DOWNDIP" },
        ]
    }

@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData.transact_update', lambda self, object_id, object_type, body: None)
class TestUpdateRuptureGenerationTask(unittest.TestCase):
    """
    All datastore (data) methods are mocked.

    TODO: more coverage please
    """
    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', TASKZERO)
    def test_update_with_metrics(self):
        qry = '''
            mutation {
                update_automation_task(input: {
                    task_id: "QXV0b21hdGlvblRhc2s6MA=="
                    duration: 909,
                    metrics: {k: "rupture_count" v: "20"}
                })
                {
                    task_result {
                        id
                        duration
                        metrics {k v}
                    }
                }
            }
        '''
        print(qry)
        executed = self.client.execute(qry)
        print(executed)
        result = executed['data']['update_automation_task']['task_result']
        assert result['id'] == 'QXV0b21hdGlvblRhc2s6MA=='
        assert result['duration'] == 909
        assert result['metrics'][0]['k'] == "rupture_count"
        assert result['metrics'][0]['v'] == "20"


#     @unittest.skip("TODO")
#     def test_merge_update_is_effective(self):
#         """need to show that the json being saved to S3 is correct"""
#         assert 0





