
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
            ruptureGenerationArgs: {
                maxJumpDistance: 55.5,
                maxSubSectionLength: 2,
                maxCumulativeAzimuth: 590}
            })
            {
                taskResult {
                id
            }
        }
    }
'''

@mock.patch('graphql_api.data_s3.BaseS3Data.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data_s3.BaseS3Data._write_object', lambda self, object_id, body: None)
class TestCreateRuptureGenerationTask(unittest.TestCase):
    """
    All S3 methods are mocked out
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
