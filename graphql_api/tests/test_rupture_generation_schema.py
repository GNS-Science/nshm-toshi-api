"""
Test API function for opensha Rupture Generation

Mocking our data layer

"""

import datetime as dt
import unittest
from unittest import mock

from dateutil.tz import tzutc
from graphene.test import Client

import graphql_api.data  # for mocking
from graphql_api.schema import root_schema

# from graphql_api.schema.file_relation import FileRelation


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

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"gitref_opensha_commons" v: "ABC"}
                { k:"gitref_opensha_core" v: "ABC"}
                { k:"nshm_nz_opensha" v: "ABC"}
                { k:"host" v:"tryharder-ubuntu"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

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


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
class TestCreateRuptureGenerationTask(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """

    def setUp(self):
        self.client = Client(root_schema)

    def test_create_minimum_fields_happy_case(self):
        executed = self.client.execute(CREATE, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(executed)
        assert (
            executed['data']['create_rupture_generation_task']['task_result']['id']
            == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        )

    def test_date_must_include_timezone(self):
        startdate = dt.datetime.now()  # no timesone
        executed = self.client.execute(CREATE, variable_values=dict(created=startdate))
        print(executed)
        assert "must have a timezone" in executed['errors'][0]['message']

    def test_date_must_be_iso_format(self):
        qry = '''
            mutation {
                create_rupture_generation_task(input: {
                    state: UNDEFINED
                    result: UNDEFINED
                    created: "September 5th, 1999"
                    })
                    {
                        task_result {
                        id
                    }
                }
            }
        '''
        startdate = dt.datetime.now()  # no timesone
        executed = self.client.execute(qry)
        print(executed)
        assert 'September 5th, 1999' in executed['errors'][0]['message']

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
        assert (
            executed['data']['create_rupture_generation_task']['task_result']['id']
            == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        )


TASKZERO = lambda _self, _id: {
    "id": "0",
    "clazz_name": "RuptureGenerationTask",
    "created": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "arguments": [
        {"k": "max_jump_distance", "v": "55.5"},
        {"k": "max_sub_section_length", "v": "2"},
        {"k": "max_cumulative_azimuth", "v": "590"},
        {"k": "min_sub_sections_per_parent", "v": "2"},
        {"k": "permutation_strategy", "v": "DOWNDIP"},
    ],
}


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
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
                update_rupture_generation_task(input: {
                    task_id: "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA="
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
        result = executed['data']['update_rupture_generation_task']['task_result']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        assert result['duration'] == 909
        assert result['metrics'][0]['k'] == "rupture_count"
        assert result['metrics'][0]['v'] == "20"

    @unittest.skip("TODO")
    def test_merge_update_is_effective(self):
        """need to show that the json being saved to S3 is correct"""
        assert 0


TASK_OLD = lambda _self, _id: {
    "id": "0",
    "clazz_name": "RuptureGenerationTask",
    "created": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "git_refs": {"opensha_ucerf3": "B", "opensha_commons": "C", "opensha_core": "A", "nshm_nz_opensha": "D"},
    "arguments": None,
    "metrics": None,
}


@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
@mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, body: None)
class TestMigrateRuptureGenerationTask(unittest.TestCase):
    """
    File "/home/chrisbc/DEV/GNS/nshm-toshi-api/graphql_api/data/thing_data.py", line 145, in from_json
        return clazz(**jsondata)
      File "/home/chrisbc/DEV/GNS/nshm-toshi-api/lib/python3.8/site-packages/graphene/types/objecttype.py", line 169, in __init__
        raise TypeError(
    TypeError: 'git_refs' is an invalid keyword argument for RuptureGenerationTask
    """

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseDynamoDBData._read_object', TASK_OLD)
    def test_transforms_old_fields(self):
        qry = '''
        query q1 {
          node(id:"UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=") {
                __typename
            id
            ... on RuptureGenerationTask {
              id
              created
              duration
              environment {
                k
                v
              }
            }
          }
        }
        '''
        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        result = executed['data']['node']
        assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
        assert result['duration'] == 600.0
        assert result['environment'][0]['k'] == "gitref_opensha-core"
        assert result['environment'][0]['v'] == "A"
