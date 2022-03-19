
"""
Test API function for GeneralTask

Mocking our data layer

"""
#from io import BytesIO
#from unittest import mock

import datetime as dt
import unittest
import boto3
import json

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb2, mock_s3
from moto.core import patch_client, patch_resource

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.schema import root_schema
from graphql_api.schema import root_schema
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject

import graphql_api.data # for mocking

QRY_CREATE_AUTOMATION_TASK = '''
    mutation ($created: DateTime!) {
        create_automation_task(input: {
            state: UNDEFINED
            result: UNDEFINED
            task_type: INVERSION
            created: $created
            duration: 600

            arguments: [
                { k:"max_jump_distance" v: "55.5" }
                { k:"permutation_strategy" v: "DOWNDIP" }
            ]

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"JAVA" v:"-Xmx24G"  }
                ]
            })
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

QRY_CREATE_AT_RELATION = '''
    mutation new_link ($thing_id: ID!, $file_id: ID!) {
      create_file_relation(
        thing_id: $thing_id
        file_id: $file_id
        role: READ
      )
      {
        ok
        file_relation { file_id }
      }
    }
'''

class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return self.next_id

TASKMOCK = lambda _self, _id: {
    "id": _id,
    "clazz_name": "GeneralTask",
    "created": "2020-10-30T09:15:00+00:00",
    "title": "max_jump_distance"
    }

ATMOCK = {'id': 0, "clazz_name": "AutomationTask",  'created': '2022-10-10T23:00:00+00:00', 'files': None, 'parents': [{'parent_id': '1', 'parent_clazz': 'GeneralTask'}], 'children': None, 'result': 'undefined', 'state': 'undefined', 'duration': 600.0, 'arguments': [{'k': 'max_jump_distance', 'v': '55.5'}, {'k': 'max_sub_section_length', 'v': '2'}, {'k': 'max_cumulative_azimuth', 'v': '590'}, {'k': 'min_sub_sections_per_parent', 'v': '2'}, {'k': 'permutation_strategy', 'v': 'DOWNDIP'}], 'environment': [{'k': 'gitref_opensha_ucerf3', 'v': 'ABC'}, {'k': 'gitref_opensha_commons', 'v': 'ABC'}, {'k': 'gitref_opensha_core', 'v': 'ABC'}, {'k': 'nshm_nz_opensha', 'v': 'ABC'}, {'k': 'host', 'v': 'tryharder-ubuntu'}, {'k': 'JAVA', 'v': '-Xmx24G'}], 'metrics': None,}
GENMOCK = {'id': 1, "clazz_name": "GeneralTask", 'created': '2022-10-10T23:00:00+00:00', 'files': None, 'parents': None, 'children': [{'child_id': '0', 'child_clazz': 'RuptureGenerationTask'}], 'updated': None, 'agent_name': 'benc', 'title': 'My Third Manual task', 'description': '##Some notes go here', 'argument_lists': None, 'swept_arguments': None, 'meta': None, 'notes': None, 'subtask_count': None, 'subtask_type': None, 'model_type': None, 'subtask_result': None}
FILEMOCK = {'id': '1587.0nVoFt',
    'file_name': 'RupSet_Cl_FM(CFM_0_9_).zip',
    'md5_digest': '5f1jFJY5keP7n7pSOX64Mg==', 'file_size': 32045903, 'file_url': None,
    'post_url': None,
    'meta': [{'k': 'max_sections', 'v': '2000'}, {'k': 'fault_model', 'v': 'CFM_0_9_SANSTVZ_D90'}, {'k': 'min_sub_sects_per_parent', 'v': '2'}, {'k': 'min_sub_sections', 'v': '2'}, {'k': 'max_jump_distance', 'v': '15'}, {'k': 'adaptive_min_distance', 'v': '6'}, {'k': 'thinning_factor', 'v': '0.2'}, {'k': 'scaling_relationship', 'v': 'TMG_CRU_2017'}],
    'relations': ['1788KuShZ', '1791WgLTz', '1792Ka2SS',
         {'id': '1568DDm7G', 'role': 'read'}, {'id': '1569hDATR', 'role': 'read'}, {'id': '15699RFaC', 'role': 'read'}],
    'clazz_name': 'File'
    }

#@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', IncrId().get_next_id)
@mock_s3
@mock_dynamodb2
class TestBug122(unittest.TestCase):
    """
    All datastore (data) methods are mocked.

    Given a legacy Rupture Set File (RSF) in (S3)
    When I create a new AutomationTask in DynamoDB
     and I link the AT to the RSF using CreateTaskFile Relation
    Then the RSF object is migrated to DynamoDB
     and the link is created
     and all the write operations are wrapped in a WriteTransaction

    """

    def setUp(self):
        self.client = Client(root_schema)
        # migrate()

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3.Bucket(S3_BUCKET_NAME)

        self._bucket.put_object(Key='FileData/1587.0nVoFt/object.json', Body=json.dumps(FILEMOCK))

    def test_create_at_and_link_file(self):

        # first AT
        at_result = self.client.execute(QRY_CREATE_AUTOMATION_TASK, variable_values=dict(created=dt.datetime.now(tzutc())))
        print(at_result)
        at_id =  at_result['data']['create_automation_task']['task_result']['id']

        assert at_id == 'QXV0b21hdGlvblRhc2s6MTAwMDAw'
        assert from_global_id(at_id) == ("AutomationTask", "100000")

        # the relation
        link_result = self.client.execute(QRY_CREATE_AT_RELATION, variable_values=dict(
            thing_id='QXV0b21hdGlvblRhc2s6MTAwMDAw',
            file_id='RmlsZToxNTg3LjBuVm9GdA=='))

        print('GTLINK ', link_result)
        assert link_result['data']['create_task_relation']['ok'] == True
                        
        # with mock.patch('graphql_api.data.BaseData._read_object', side_effect=[ATMOCK, GENMOCK, GENMOCK]):
        #     ruptgen_parent_query = self.client.execute(QUERY_RUPTGEN_PARENT, variable_values=dict(created=dt.datetime.now(tzutc())))
        #     print('RUPTGEN_PARENT', ruptgen_parent_query)
        #     result = ruptgen_parent_query['data']['node']
        #     assert result['parents']['edges'][0]['node']['parent']\
        #                 ['id'] == "R2VuZXJhbFRhc2s6MQ=="
        #     assert result['parents']['edges'][0]['node']['parent']\
        #                 ['title'] == "My Third Manual task"
        #     assert result['parents']['edges'][0]['node']['parent']\
        #                 ['description'] == "##Some notes go here"
        #     assert result['id'] == 'UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA='
