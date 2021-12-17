
"""
Test Elastic Serach via SearchManager

Mocking out ES in requests

"""
# from io import BytesIO
# from unittest import mock

# import datetime as dt
import unittest

# from dateutil.tz import tzutc

# from graphql_api import data_s3

from graphene.test import Client
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager
from .fixtures import es_query_response as eqr
from graphql_api.schema import File

from unittest import mock
import requests_mock

FAKE_ENDPOINT = 'http://localhost:9200' #matches default local setup
FAKE_INDEX = 'toshi-index'
awsauth = None


class TestSearchManager(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)
        self.search_manager = SearchManager(endpoint=FAKE_ENDPOINT, es_index=FAKE_INDEX, awsauth=awsauth)

    def test_setup(self):
        assert isinstance(self.search_manager, SearchManager)

    def test_query_with_mock_requests(self):
        with requests_mock.Mocker() as m:
            url = FAKE_ENDPOINT + '/' + FAKE_INDEX + '/_search?q=560'
            #url = "http://fake.es_search/endpoint/toshi_index/_search?q=560"
            m.get(url, content=eqr.response_01) #set up the mocking

            result = self.search_manager.search("560")
            res0 = [r for r in result][0]
            print(res0)
            # assert 0
            assert isinstance(res0, File)


class TestSchemaSearch(unittest.TestCase):
    """
    """
    def setUp(self):
        self.client = Client(root_schema)

    def test_query_with_mock_requests(self):

        qry = '''
            query m1 {
              search(search_term:"560") {

                search_result {
                    total_count
                    edges {
                        node {
                            ... on RuptureGenerationTask {
                                id
                                state
                                created
                            }
                            ... on File {
                                id
                                file_name
                                md5_digest
                            }
                        }
                    }
                }
              }
            }
        '''
        with requests_mock.Mocker() as m:
            url = FAKE_ENDPOINT + '/' + FAKE_INDEX + '/_search?q=560'
            m.get(url, content=eqr.response_01) #set up the mocking

            executed = self.client.execute(qry)
            print(executed)
            assert executed['data']['search']['search_result']['total_count'] == 3


# def mock_make_api_call(self, operation_name, kwarg):
#     raise ValueError("query fired an (expensive) S3 API operation: ", operation_name)

# @mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call)
class TestSchemaSearchTotalCount(unittest.TestCase):
    """
    All datastore (data_s3) methods are mocked.
    """
    def setUp(self):
        self.client = Client(root_schema)
        #monkey patching
        schema_sm = SearchManager(endpoint=FAKE_ENDPOINT, es_index=FAKE_INDEX, awsauth=awsauth)

    def test_relations_only_total_count(self):
        qry = '''
            query m1 {
              search(search_term:"560") {
                search_result {
                total_count
                  edges {
                    node {
                      ... on File {
                        id
                        relations {
                          total_count
                          # edges {
                          #   node {
                          #     id
                          #   }
                          # }
                        }
                      }
                    }
                  }
                }
              }
            }
        '''

        # from hashlib import sha256, md5
        with requests_mock.Mocker() as m:
            url = FAKE_ENDPOINT + '/' + FAKE_INDEX + '/_search?q=560'
            m.get(url, content=eqr.response_01) #set up the mocking

            executed = self.client.execute(qry,
                variable_values={})
            print(executed)
            assert executed['data']['search']['search_result']['total_count'] == 3
            assert executed['data']['search']['search_result']['edges'][0]['node']['relations']['total_count'] == 1


    def test_traversing_into_s3_api_call(self): 
        qry = '''

            query m1 {
              search(search_term:"560") {
                search_result {
                total_count
                  edges {
                    node {
                      ... on File {
                           id
                        relations {
                          total_count
                          edges {
                            node {
                              file_id
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
        '''

        # from hashlib import sha256, md5
        with requests_mock.Mocker() as m:
            url = FAKE_ENDPOINT + '/' + FAKE_INDEX + '/_search?q=560'
            m.get(url, content=eqr.response_01) #set up the mocking

            executed = self.client.execute(qry,
                variable_values={})

            print('EXECUTED:', executed)
            assert executed['data']['search']['search_result']['total_count'] == 3

