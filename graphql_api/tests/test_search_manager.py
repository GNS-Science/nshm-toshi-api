
"""
Test Elastic Serach via SearchManager

Mocking out ES in requests

"""
# from io import BytesIO
# from unittest import mock

# import datetime as dt
import unittest

# from dateutil.tz import tzutc

# from graphene.test import Client
from graphql_api import data_s3

from graphql_api.schema import search_manager as sm

from .fixtures import es_query_response as eqr


FAKE_ENDPOINT = 'http://fake.es_search/endpoint'
FAKE_INDEX = 'tohsi_index'
awsauth = None

class TestSearchManager(unittest.TestCase):
    """
    """

    def setUp(self):
    	self.search_manager = sm.SearchManager(endpoint=FAKE_ENDPOINT, es_index=FAKE_INDEX, awsauth=awsauth)

    def test_setup(self):
    	assert isinstance(self.search_manager, sm.SearchManager)
