
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
# from graphql_api.schema.file_relation import FileRelation

import graphql_api.data_s3 # for mocking


CREATE = '''
    mutation ($created: DateTime!) {
        create_rupture_generation_task(input: {
            state: UNDEFINED
            result: UNDEFINED
            created: $created
            duration: 600
            arguments: [
                { k:"max_jump_distance" v: "55.5" }
                { k:"max_sub_section_length" v: "2" }
                { k:"max_cumulative_azimuth" v: "590" }
                { k:"min_sub_sections_per_parent" v: "2" }
                { k:"permutation_strategy" v: "DOWNDIP" }
            ]
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
                created
                duration
                arguments {k v}
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
            variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['create_rupture_generation_task']\
                        ['task_result']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='

    def test_date_must_include_timezone(self):
        startdate = dt.datetime.now() #no timesone
        executed = self.client.execute(CREATE, variable_values=dict(created=startdate))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                create_rupture_generation_task(input: {
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

    @unittest.skip('deprecated behaviour')
    def test_create_with_metrics_needs_all_or_none(self):
        insert = '''
            rupture_count: 20

            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)

        print(qry)
        executed = self.client.execute(qry, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert 'In field "metrics": In field "subsection_count":'\
                ' Expected "Int!", found null.' in executed['errors'][0]['message']


    def test_create_with_metrics(self):
        insert = '''
            rupture_count: 20
            '''
        qry = CREATE.replace('##EXTRA_INPUT##', insert)
        print(qry)
        executed = self.client.execute(qry, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert executed['data']['create_rupture_generation_task']\
                        ['task_result']['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='


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
                    rupture_count: 20
                })
                {
                    task_result {
                        id
                        duration
                        rupture_count
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
        assert result['rupture_count'] == 20


    @unittest.skip("TODO")
    def test_merge_update_is_effective(self):
        """need to show that the json being saved to S3 is correct"""
        assert 0

