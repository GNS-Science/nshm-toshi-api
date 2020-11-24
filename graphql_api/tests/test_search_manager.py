
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
from graphql_api.schema import search_manager as sm
from .fixtures import es_query_response as eqr
from graphql_api.schema import File
import requests_mock

FAKE_ENDPOINT = 'http://fake.es_search/endpoint'
FAKE_INDEX = 'toshi_index'
awsauth = None


class TestSearchManager(unittest.TestCase):
    """
    """

    def setUp(self):
        self.client = Client(root_schema)
        self.search_manager = sm.SearchManager(endpoint=FAKE_ENDPOINT, es_index=FAKE_INDEX, awsauth=awsauth)

    def test_setup(self):
        assert isinstance(self.search_manager, sm.SearchManager)

    def test_query_with_mock_requests(self):
        with requests_mock.Mocker() as m:
            url = FAKE_ENDPOINT + '/' + FAKE_INDEX + '/_search?q=560'
            #url = "http://fake.es_search/endpoint/toshi_index/_search?q=560"
            m.get(url, content=eqr.response_01) #set up the mocking

            result = self.search_manager.search("560")
            res0 = [r for r in result][0]
            print(res0)
            assert isinstance(res0, File)



SEARCH = '''
    query m1 {
      search(search_term:"560") {

        search_result {
            total_count
            edges {
                node {
                    ... on RuptureGenerationTask {
                        id
                        state
                        started
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

class TestSchemaSearch(unittest.TestCase):
    """
    """


    def setUp(self):
        self.client = Client(root_schema)

    def test_query_with_mock_requests(self):
        with requests_mock.Mocker() as m:
            url = "http://es.none/_none/_search?q=560"
            m.get(url, content=eqr.response_01) #set up the mocking

            executed = self.client.execute(SEARCH)
            print(executed)
            assert executed['data']['search']['search_result']['total_count'] == 11