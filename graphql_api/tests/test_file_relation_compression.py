import datetime as dt
import json
import random
import unittest

import boto3
from dateutil.tz import tzutc
from graphene.test import Client
from graphql_relay import to_global_id
from moto import mock_dynamodb, mock_s3
from nzshm_common.util import compress_string, decompress_string
from pynamodb.connection.base import Connection  # for mocking

import graphql_api.data.file_relation_data
from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.data.file_data import FileData
from graphql_api.data.thing_data import ThingData
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

# Monkey patch for testing
UNCOMPRESSED_LIMIT = 25
graphql_api.data.file_relation_data.UNCOMPRESSED_LIMIT = UNCOMPRESSED_LIMIT

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
    'id': '100000',
    "clazz_name": "AutomationTask",
    'created': dt.datetime.now(tzutc()),
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
FAKE_RELATION = {'id': '100000', 'role': 'read'}
# FILE_RELATIONS = compress_string(json.dumps([FAKE_RELATION for x in range(UNCOMPRESSED_LIMIT )]))
FILE_RELATIONS = [FAKE_RELATION for x in range(UNCOMPRESSED_LIMIT)]
FILEMOCK = {
    'id': '100000',
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
    'relations': FILE_RELATIONS,
    'clazz_name': 'File',
}


@mock_s3
@mock_dynamodb
class TestCompressRelations(unittest.TestCase):
    def setUp(self):
        self.client = Client(root_schema)

        # S3 is used for file object storage
        self._s3_conn = boto3.resource('s3', region_name=REGION)
        self._s3_conn.create_bucket(Bucket=S3_BUCKET_NAME)
        self._bucket = self._s3_conn.Bucket(S3_BUCKET_NAME)
        self._connection = Connection(region=REGION)

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', {'fake': 'auth'}))
        at1 = ThingData({}, self._data_manager, ToshiThingObject, self._connection)
        at1.create(**ATMOCK)  # will get identity 100000 = 'QXV0b21hdGlvblRhc2s6MTAwMDAw',
        f1 = FileData({}, self._data_manager, ToshiFileObject, self._connection)
        f1.create(**FILEMOCK)

    # @unittest.skip('experimental test code')
    def test_how_many_relations_in_390k(self):
        def fake_relation():
            return {'id': random.randint(int(1e5), int(1e7)), 'role': random.choice(['read'])}

        MAX_RELS = int(80e3)  # 0000
        MAX_SIZE = 390e3  # 3000

        rels = [fake_relation() for x in range(MAX_RELS)]
        size = len(compress_string(json.dumps(rels)))
        print(size)
        self.assertTrue(size < MAX_SIZE)

    def test_create_file_relation_added_with_compression(self):
        file_id = to_global_id(FILEMOCK['clazz_name'], FILEMOCK['id'])

        # the relation
        link_result = self.client.execute(
            QRY_CREATE_AT_RELATION, variable_values=dict(thing_id='QXV0b21hdGlvblRhc2s6MTAwMDAw', file_id=file_id)
        )

        print(link_result)
        assert link_result['data']['create_file_relation']['ok'] == True

        # get the file back from dyamodb
        file = ToshiFileObject.get(FILEMOCK['id'])
        print(file.object_content)
        self.assertEqual(len(json.loads(decompress_string(file.object_content['relations']))), UNCOMPRESSED_LIMIT + 1)
        self.assertEqual(
            json.loads(decompress_string(file.object_content['relations']))[-1], {'id': '100000', 'role': 'read'}
        )

    def test_round_trip_file_relation_with_compression(self):
        file_id = to_global_id(FILEMOCK['clazz_name'], FILEMOCK['id'])

        link_result = self.client.execute(
            QRY_CREATE_AT_RELATION, variable_values=dict(thing_id='QXV0b21hdGlvblRhc2s6MTAwMDAw', file_id=file_id)
        )

        file = ToshiFileObject.get(FILEMOCK['id'])
        # print(file.object_content)
        self.assertEqual(len(json.loads(decompress_string(file.object_content['relations']))), UNCOMPRESSED_LIMIT + 1)
        self.assertEqual(
            json.loads(decompress_string(file.object_content['relations']))[-1], {'id': '100000', 'role': 'read'}
        )

        query = (
            '''
            query get_file {
              node(id: "%s") {
                ... on File {
                  file_name
                  file_size
                  relations {
                    total_count
                    edges {
                      node {
                        ... on FileRelation {
                          role
                          thing {
                            ... on Node{
                              id
                              __typename
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }'''
            % file_id
        )

        file_result = self.client.execute(query)
        # print(file_result)
        self.assertEqual(file_result['data']['node']['relations']['total_count'], UNCOMPRESSED_LIMIT + 1)
        self.assertEqual(
            file_result['data']['node']['relations']['edges'][0]['node']['thing']['id'], 'QXV0b21hdGlvblRhc2s6MTAwMDAw'
        )
        self.assertEqual(
            file_result['data']['node']['relations']['edges'][0]['node']['thing']['__typename'], 'AutomationTask'
        )
