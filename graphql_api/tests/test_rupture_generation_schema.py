
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

from graphql_api.schema import root_schema, RuptureGenerationTask

import graphql_api.data_s3 # for mocking


CREATE = '''
    mutation ($started: DateTime!) {
        create_rupture_generation_task(input: {
            state: UNDEFINED
            result: UNDEFINED
            started: $started
            duration: 600
            arguments: {
                max_jump_distance: 55.5
                max_sub_section_length: 2
                max_cumulative_azimuth: 590
                min_sub_sections_per_parent: 2
                permutation_strategy: DOWNDIP
                }
            git_refs: {
                opensha_ucerf3: "ABC"
                opensha_commons: "ABC"
                opensha_core: "ABC"
                nshm_nz_opensha: "ABC"
            }
            ##EXTRA_INPUT##
            }
            )
            {
                task_result {
                id
                started
                duration
                arguments { max_jump_distance }
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
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE,
            variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['create_rupture_generation_task']\
                        ['task_result']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='

    def test_date_must_include_timezone(self):
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(CREATE, variable_values=dict(started=startdate))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                create_rupture_generation_task(input: {
                    started: "September 5th, 1999"
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

    @unittest.skip('deprecated behaviour')
    def test_create_with_metrics_needs_all_or_none(self):
        insert = '''
            metrics: {
             rupture_count: 20
            }
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)

        print(qry)
        executed = self.client.execute(qry, variable_values=dict(started=dt.datetime.now(tzutc())))
        print(executed)
        assert 'In field "metrics": In field "subsection_count":'\
                ' Expected "Int!", found null.' in executed['errors'][0]['message']


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
        assert executed['data']['create_rupture_generation_task']\
                        ['task_result']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='


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

    TODO: more coverage please
    """
    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', TASKZERO)
    def test_update_with_metrics(self):
        qry = '''
            mutation {
                update_rupture_generation_task(input: {
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
        result = executed['data']['update_rupture_generation_task']['task_result']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        assert result['duration'] == 909
        assert result['metrics']['rupture_count'] == 20


    @unittest.skip("TODO")
    def test_merge_update_is_effective(self):
        """need to show that the json being saved to S3 is correct"""
        assert 0

