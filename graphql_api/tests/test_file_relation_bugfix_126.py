import datetime as dt
import json
import unittest
from io import BytesIO

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id
from moto import mock_dynamodb, mock_s3
from moto.core import patch_client, patch_resource
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.data.thing_data import ThingData
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

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
    mutation ($thing_id: ID!, $file_id: ID!) {
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


ATMOCK = {
    'id': 0,
    "clazz_name": "AutomationTask",
    'created': '2022-10-10T23:00:00+00:00',
    'files': None,
    'parents': [{'parent_id': '1', 'parent_clazz': 'GeneralTask'}],
    'children': None,
    'result': 'undefined',
    'state': 'undefined',
    'duration': 600.0,
    'arguments': [
        {'k': 'max_jump_distance', 'v': '55.5'},
        {'k': 'max_sub_section_length', 'v': '2'},
        {'k': 'max_cumulative_azimuth', 'v': '590'},
        {'k': 'min_sub_sections_per_parent', 'v': '2'},
        {'k': 'permutation_strategy', 'v': 'DOWNDIP'},
    ],
    'environment': [
        {'k': 'gitref_opensha_ucerf3', 'v': 'ABC'},
        {'k': 'gitref_opensha_commons', 'v': 'ABC'},
        {'k': 'gitref_opensha_core', 'v': 'ABC'},
        {'k': 'nshm_nz_opensha', 'v': 'ABC'},
        {'k': 'host', 'v': 'tryharder-ubuntu'},
        {'k': 'JAVA', 'v': '-Xmx24G'},
    ],
    'metrics': None,
}
FILEMOCK = {
    'id': '1587.0nVoFt',
    'file_name': 'RupSet_Cl_FM(CFM_0_9_).zip',
    'md5_digest': '5f1jFJY5keP7n7pSOX64Mg==',
    'file_size': 32045903,
    'file_url': None,
    'post_url': None,
    'meta': [
        {'k': 'max_sections', 'v': '2000'},
        {'k': 'fault_model', 'v': 'CFM_0_9_SANSTVZ_D90'},
        {'k': 'min_sub_sects_per_parent', 'v': '2'},
        {'k': 'min_sub_sections', 'v': '2'},
        {'k': 'max_jump_distance', 'v': '15'},
        {'k': 'adaptive_min_distance', 'v': '6'},
        {'k': 'thinning_factor', 'v': '0.2'},
        {'k': 'scaling_relationship', 'v': 'TMG_CRU_2017'},
    ],
    'relations': [
        '1788KuShZ',
        '1791WgLTz',
        '1792Ka2SS',
        {'id': '1568DDm7G', 'role': 'read'},
        {'id': '1569hDATR', 'role': 'read'},
        {'id': '15699RFaC', 'role': 'read'},
    ],
    'clazz_name': 'File',
}


@mock_s3
@mock_dynamodb
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

        self._s3_conn = boto3.resource('s3', region_name=REGION)
        self._s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3_conn.Bucket(S3_BUCKET_NAME)
        self._connection = Connection(region=REGION)

        self._bucket.put_object(Key='FileData/1587.0nVoFt/object.json', Body=json.dumps(FILEMOCK))
        self._bucket.put_object(Key='ThingData/100002/object.json', Body=json.dumps({'id': '100002'}))

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))
        at1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        at1.create(
            clazz_name='AutomationTask', created=dt.datetime.now(tzutc())
        )  # will get identity 100000 = 'QXV0b21hdGlvblRhc2s6MTAwMDAw',

    def test_s3_create(self):
        # bucket S3_BUCKET_NAME_unconfigured, key=FileData/1587.0nVoFt/object.json, client=
        print(f"S3_BUCKET_NAME {S3_BUCKET_NAME}")
        assert S3_BUCKET_NAME == "S3_BUCKET_NAME_unconfigured"
        s3obj = self._s3_conn.Object(S3_BUCKET_NAME, 'ThingData/100002/object.json')
        file_object = BytesIO()
        s3obj.download_fileobj(file_object)
        file_object.seek(0)

        obj = json.load(file_object)
        assert obj['id'] == '100002'

    def test_s3_config_for_test(self):
        # bucket S3_BUCKET_NAME_unconfigured, key=FileData/1587.0nVoFt/object.json, client=
        print(f"S3_BUCKET_NAME {S3_BUCKET_NAME}")
        assert S3_BUCKET_NAME == "S3_BUCKET_NAME_unconfigured"
        s3obj = self._s3_conn.Object(S3_BUCKET_NAME, 'FileData/1587.0nVoFt/object.json')
        file_object = BytesIO()
        s3obj.download_fileobj(file_object)
        file_object.seek(0)

        obj = json.load(file_object)
        assert obj['id'] == '1587.0nVoFt'

    def test_create_file_relation(self):
        file_id = to_global_id(FILEMOCK['clazz_name'], FILEMOCK['id'])

        # the relation
        link_result = self.client.execute(
            QRY_CREATE_AT_RELATION, variable_values=dict(thing_id='QXV0b21hdGlvblRhc2s6MTAwMDAw', file_id=file_id)
        )

        assert link_result['data']['create_file_relation']['ok'] == True

    def test_create_at(self):
        # Create a new AT
        at_result = self.client.execute(
            QRY_CREATE_AUTOMATION_TASK, variable_values=dict(created=dt.datetime.now(tzutc()))
        )
        print(at_result)
        at_id = at_result['data']['create_automation_task']['task_result']['id']

        assert at_id == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        assert from_global_id(at_id) == ("AutomationTask", "100001")

    def test_create_at_and_link_file(self):
        # Create a new AT
        at_result = self.client.execute(
            QRY_CREATE_AUTOMATION_TASK, variable_values=dict(created=dt.datetime.now(tzutc()))
        )
        print(at_result)
        at_id = at_result['data']['create_automation_task']['task_result']['id']

        # assert at_id == 'QXV0b21hdGlvblRhc2s6MTAwMDAx'
        # assert from_global_id(at_id) == ("AutomationTask", "100001")

        file_id = to_global_id(FILEMOCK['clazz_name'], FILEMOCK['id'])

        # the relation
        link_result = self.client.execute(QRY_CREATE_AT_RELATION, variable_values=dict(thing_id=at_id, file_id=file_id))

        assert link_result['data']['create_file_relation']['ok'] == True
