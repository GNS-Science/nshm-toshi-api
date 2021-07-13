
"""
Test API function for InversionSolution
Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data_s3

from graphql_api.schema import root_schema
from graphql_api.schema.custom.inversion_solution import InversionSolution, CreateInversionSolution

import graphql_api.data_s3 # for mocking

class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return str(self.next_id) + 'RANDM'

READ_MOCK = lambda _self, id: dict(
    id = "0i93qK",
    clazz_name = "InversionSolution",
    md5_digest = "$digest",
    file_name = "$file_name",
    file_size = "$file_size",
    produced_by = "$produced_by",
    mfd_table = "$mfd_table",
    )

@mock.patch('graphql_api.data_s3.file_data.FileData.get_next_id', IncrId().get_next_id)
@mock.patch('graphql_api.data_s3.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})
class TestBasicInversionSolutionOperations(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """
    def setUp(self):
        self.client = Client(root_schema)

    # @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_create_bare_table(self):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $produced_by: ID!, $mfd_table: ID!) {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by: $produced_by
                  mfd_table: $mfd_table
                  }
              ) {
              inversion_solution { id }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID", mfd_table="TABLE_ID"))
        print(result)
        assert result['data']['create_inversion_solution']['inversion_solution']['id'] == 'SW52ZXJzaW9uU29sdXRpb246Tm9uZQ=='

    @mock.patch('graphql_api.data_s3.BaseS3Data._read_object', READ_MOCK)
    def test_get_inversion_solution_by_node_id(self):
        # the first GT
        qry = '''
        query get_FDT {
          node(id:"VGFibGU6MA==") {
            __typename
            ... on InversionSolution {
              #created
              id
              file_name
              produced_by
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'SW52ZXJzaW9uU29sdXRpb246MGk5M3FL'
        assert result['data']['node']['file_name'] == "$file_name"
        assert result['data']['node']['produced_by'] == "$produced_by"
