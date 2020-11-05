
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
from graphql_api import data_s3

from graphql_api.schema import schema, RuptureGenerationTask

import graphql_api.data_s3 # for mocking


CREATE = '''
    mutation ($started: DateTime!) {
        createRuptureGenerationTask(input: {
            started: $started,
            duration: 600,
            arguments: {
                maxJumpDistance: 55.5,
                maxSubSectionLength: 2,
                maxCumulativeAzimuth: 590
                minSubSectionsPerParent: 2
                permutationStrategy: DOWNDIP
                openshaUcerf3GitRef: "ABC"
                openshaCommonsGitRef: "ABC"
                openshaCoreGitRef: "ABC"
                nshmNzOpenshaGitRef: "ABC"
                }
            ##EXTRA_INPUT##
            }
            )
            {
                taskResult {
                id
                started
                duration
                arguments { maxJumpDistance }
            }
        }
    }
'''




@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestCreateRuptureGenerationTask(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """

    def setUp(self):
        self.client = Client(schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE,
            variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['createRuptureGenerationTask']\
                        ['taskResult']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='

    def test_date_must_include_timezone(self):
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(CREATE, variable_values=dict(started=startdate))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                createRuptureGenerationTask(input: {
                    started: "September 5th, 1999"
                    })
                    {
                        taskResult {
                        id
                    }
                }
            }
        '''
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(qry)
        print(executed)
        assert 'Expected type "DateTime", found "September 5th, 1999"' in executed['errors'][0]['message']


    def test_create_with_metrics_needs_all_or_none(self):
        insert = '''
            metrics: {
             ruptureCount: 20
            }
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)

        print(qry)
        executed = self.client.execute(qry, variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert 'In field "metrics": In field "subsectionCount":'\
                ' Expected "Int!", found null.' in executed['errors'][0]['message']


    def test_create_with_metrics(self):
        insert = '''
            metrics: {
             ruptureCount: 20
             subsectionCount: 20
             clusterConnectionCount: 20
            }
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)
        print(qry)
        executed = self.client.execute(qry, variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['createRuptureGenerationTask']\
                        ['taskResult']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='


TASKZERO = lambda _self, _id: {
    "id": "0",
    "started": "2020-10-30T09:15:00+00:00",
    "duration": 600.0, "input_files": ["0"],
    "arguments": {"max_jump_distance": 55.5, "max_sub_section_length": 2.0, "max_cumulative_azimuth": 590.0}
    }

@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestUpdateRuptureGenerationTask(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """
    def setUp(self):
        self.client = Client(schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', TASKZERO)
    def test_update_with_metrics(self):
        qry = '''
            mutation {
                updateRuptureGenerationTask(input: {
                    taskId: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA="
                    duration: 909,
                    metrics: {
                        ruptureCount: 20
                        subsectionCount: 20
                        clusterConnectionCount: 20
                    }
                })
                {
                    taskResult {
                        id
                        duration
                        metrics {
                            ruptureCount
                        }
                    }
                }
            }
        '''
        print(qry)
        executed = self.client.execute(qry)
        print(executed)
        result = executed['data']['updateRuptureGenerationTask']['taskResult']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        assert result['duration'] == 909
        assert result['metrics']['ruptureCount'] == 20

