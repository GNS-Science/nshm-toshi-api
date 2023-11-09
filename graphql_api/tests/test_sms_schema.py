"""
Test API function for SMS

Mocking our data layer

"""
import datetime as dt
import unittest
from io import BytesIO
from unittest import mock

from dateutil.tz import tzutc
from graphene.test import Client

import graphql_api.data  # for mocking
from graphql_api import data
from graphql_api.schema import root_schema
from graphql_api.schema.custom import StrongMotionStation

CREATE = '''
    mutation ($created: DateTime!) {
        create_strong_motion_station(input: {
            created: $created
            #updated: $updated
            ##EXTRA_INPUT##
            }
            )
            {
                strong_motion_station {
                id
                created
            }
        }
    }
'''


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
class TestCreateSMS(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert (
            executed['data']['create_strong_motion_station']['strong_motion_station']['id']
            == 'U3Ryb25nTW90aW9uU3RhdGlvbjow'
        )

    def test_created_date_must_include_timezone(self):
        created = dt.datetime.now()  # no timesone
        executed = self.client.execute(CREATE, variable_values=dict(created=created))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                create_strong_motion_station(input: {
                    created: "September 5th, 1999"
                    })
                    {
                        strong_motion_station {
                        id
                    }
                }
            }
        '''
        startdate = dt.datetime.now()  # no timesone
        executed = self.client.execute(qry)
        print(executed)
        assert 'Expected type "DateTime", found "September 5th, 1999"' in executed['errors'][0]['message']

    @unittest.skip("not there yet")
    def test_create_with_metrics(self):
        insert = '''
            metrics: {
             rupture_count: 20
             subsection_count: 20
             cluster_connection_count: 20
            }
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)
        print(qry)
        executed = self.client.execute(qry, variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert (
            executed['data']['create.rupture_generation_task_task']['task_result']['id']
            == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        )


TASKZERO = lambda _self, _id: {
    "id": "0",
    "started": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "input_files": ["0"],
    "arguments": {"max_jump_distance": 55.5, "max_sub_section_length": 2.0, "max_cumulative_azimuth": 590.0},
}


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
class TestUpdateSMS(unittest.TestCase):
    """
    All datastore (data) methods are mocked.

    TODO: more coverage please
    """

    def setUp(self):
        self.client = Client(root_schema)

    @unittest.skip("not there yet")
    @mock.patch('graphql_api.data.BaseData._read_object', TASKZERO)
    def test_update_with_metrics(self):
        qry = '''
            mutation {
                update.rupture_generation_task_task(input: {
                    task_id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA="
                    duration: 909,
                    metrics: {
                        rupture_count: 20
                        subsection_count: 20
                        cluster_connection_count: 20
                    }
                })
                {
                    task_result {
                        id
                        duration
                        metrics {
                            rupture_count
                        }
                    }
                }
            }
        '''
        print(qry)
        executed = self.client.execute(qry)
        print(executed)
        result = executed['data']['update.rupture_generation_task_task']['task_result']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        assert result['duration'] == 909
        assert result['metrics']['rupture_count'] == 20

    @unittest.skip("TODO")
    def test_merge_update_is_effective(self):
        """need to show that the json being saved to S3 is correct"""
        assert 0
