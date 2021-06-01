
"""
Test API function for opensha Rupture Generation related files

Mocking our data layer

"""
import unittest
from copy import copy
from unittest import mock

# from graphql_api.data_s3 import get_data_manager
# from graphql_api.data_s3.data_manager import DataManager
from graphql_api.data_s3.s3_write_through_cache import S3WriteThroughCache

# import botocore
# import boto3
import json
from io import BytesIO

import datetime
from dateutil.tz import tzutc
from botocore.response import StreamingBody
import time

# orig = botocore.client.BaseClient._make_api_call


GENTASK = {
    "id": "0zHJ450",
    "clazz_name": "RuptureGenerationTask",
    "created": "2020-10-30T09:15:00+00:00",
    "duration": 600.0,
    "arguments": None,
    "metrics": None,
    "files": ["0V437F"]
    }

GENHEAD = {'ResponseMetadata': {'HTTPStatusCode': 200,
            'HTTPHeaders': {'accept-ranges': 'bytes', 'content-type': 'binary/octet-stream',
            'last-modified': 'Tue, 01 Jun 2021 02:24:56 GMT', 'etag': '"afc14ddff5f28e3bce4824e8f47e9303"',
            'content-length': '250', 'date': 'Tue, 01 Jun 2021 04:02:48 GMT', 'connection': 'keep-alive'},
            'RetryAttempts': 0}, 'AcceptRanges': 'bytes',
            'LastModified': datetime.datetime(2021, 6, 1, 2, 24, 56, tzinfo=tzutc()),
            'ContentLength': 250, 'ETag': '"afc14ddff5f28e3bce4824e8f47e9303"', 'ContentType': 'binary/octet-stream', 'Metadata': {}
            }


def mock_make_api_call(operation_name, kwarg):

    result = None
    print(operation_name)
    if operation_name == 'HeadObject':
        # Your Operation here!
        result = copy(GENHEAD)
    elif operation_name == 'GetObject':
        result = copy(GENHEAD)
        encoded_message = json.dumps(GENTASK).encode("utf-8")
        result['Body'] = StreamingBody(BytesIO(encoded_message), len(encoded_message))
    elif operation_name == 'PutObject':
        pass
    else:
        # result =  orig( operation_name, kwarg)
        assert False
    #print(result)
    return result

#@mock.patch('graphql_api.data_s3.s3_write_through_cache.boto3.client')
#@mock.patch('graphql_api.data_s3.s3_write_through_cache.boto3.resource')
@mock.patch('graphql_api.data_s3.s3_write_through_cache.botocore.client.BaseClient._make_api_call')
class TestCacheConfig(unittest.TestCase):

    def setUp(self):

        self.client_args = dict(aws_access_key_id='S3RVER',
            aws_secret_access_key='S3RVER',
            endpoint_url='http://localhost:4569')
        # awsauth = None
        # ES_ENDPOINT = "http://localhost:9200"
        # ES_INDEX = "toshi-index"

    def test_default_cache_setup(self, mocked_s3, *mocked_boto3):
        cache = S3WriteThroughCache(self.client_args)

    def test_read_uncached_object(self, mocked_s3, *mocked_boto3):

        mocked_s3.side_effect = mock_make_api_call

        cache = S3WriteThroughCache(self.client_args)

        fetched = cache.read_through("ThingData/1HGAq8/object.json")

        print(mocked_s3.mock_calls)

        assert fetched == GENTASK
        assert mocked_s3.call_count == 2 #S3 API was called twice HEAD and GET

    #@unittest.skip("not there yet")
    def test_read_cached_object(self, mocked_s3, *mocked_boto3):

        mocked_s3.side_effect = mock_make_api_call

        cache = S3WriteThroughCache(self.client_args)
        fetched = cache.read_through("ThingData/1HGAq8/object.json")

        assert fetched == GENTASK
        assert mocked_s3.call_count == 2 #S3 API was called twice

        time.sleep(0.01) #force cache aging
        fetched = cache.read_through("ThingData/1HGAq8/object.json")
        assert fetched == GENTASK
        assert mocked_s3.call_count == 2 #S3 API not called again

        assert len(cache) == 1

    #@unittest.skip("not there yet")
    def test_write_cached_object(self, mocked_s3, *mocked_boto3):

        mocked_s3.side_effect = mock_make_api_call

        cache = S3WriteThroughCache(self.client_args)
        result = cache.write_through("ThingData/NEW1/object.json", copy(GENTASK))

        assert mocked_s3.call_count == 1 #S3 API was called once PUT

        fetched = cache.read_through("ThingData/NEW1/object.json")
        assert fetched == GENTASK
        assert mocked_s3.call_count == 1 #S3 API not called again no READ






