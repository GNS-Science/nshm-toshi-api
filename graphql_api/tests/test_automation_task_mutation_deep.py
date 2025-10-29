"""
Test API function for opensha Rupture Generation

Mocking our data layer

"""

import datetime as dt
import unittest
from unittest import mock

import boto3
from dateutil.tz import tzutc
from elasticsearch import Elasticsearch
from graphene.test import Client
from moto import mock_dynamodb, mock_s3
from pynamodb.connection.base import Connection  # for mocking

from graphql_api.config import REGION, S3_BUCKET_NAME
from graphql_api.data import data_manager
from graphql_api.dynamodb.models import ToshiFileObject, ToshiIdentity, ToshiThingObject
from graphql_api.schema import root_schema
from graphql_api.schema.search_manager import SearchManager

from .hazard.setup_helpers import SetupHelpersMixin

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


@mock_s3
@mock_dynamodb
class TestUpdateRuptureGenerationTask(unittest.TestCase, SetupHelpersMixin):
    """
    All datastore (data) methods are mocked.

    TODO: more coverage please
    """

    @mock.patch('graphql_api.schema.search_manager.Elasticsearch')
    def setUp(self, mock_es_class):
        self.client = Client(root_schema)
        # S3
        self._s3 = boto3.resource('s3', region_name=REGION)
        self._s3.create_bucket(Bucket=S3_BUCKET_NAME)

        # Dynamo
        self._connection = Connection(region=REGION)

        # Configure the mock search method to return a predefined response
        self.mock_es_instance = mock.MagicMock()
        mock_es_class.return_value = self.mock_es_instance
        self.mock_es_instance.index.return_value = {"A": "B"}

        ToshiThingObject.create_table()
        ToshiFileObject.create_table()
        ToshiIdentity.create_table()

        self._data_manager = data_manager.DataManager(search_manager=SearchManager('test', 'test', 'fake:auth'))

        upstream_sid = self.create_source_solution()
        self.new_gt = self.create_general_task()
        self.at_id = self.create_automation_task("SCALE_SOLUTION")
        self.create_gt_relation(self.new_gt, self.at_id)
        assert len(self.mock_es_instance.index.mock_calls) == 5
        result = self.create_scaled_solution(upstream_sid, self.at_id)
        assert len(self.mock_es_instance.index.mock_calls) == 6

        ss = result['data']['create_scaled_inversion_solution']['solution']
        # self.assertEqual(ss['source_solution']['id'], upstream_sid)

        # print(ToshiFileObject.get("100001").object_content)

        # # object ID is stored internally as an INT
        # self.assertEqual(ToshiFileObject.get("100001").object_content['id'], int(from_global_id(ss['id'])[1]))
        self.scaled_solution_id = ss['id']

    def test_update_with_metrics(self):
        qry = (
            '''
            mutation {
                update_automation_task(input: {
                    task_id: "%s"
                    duration: 909,
                    metrics: {k: "rupture_count" v: "20"}
                    state: DONE
                    result: SUCCESS
                })
                {
                    task_result {
                        id
                        duration
                        metrics {k v}
                        result
                        state
                    }
                }
            }
        '''
            % self.at_id
        )
        print(qry)
        executed = self.client.execute(qry)
        print(executed)

        # mock_es_instance.index.assert_called_once_with(
        #     index='my_index', body={'query': {'match': {'field': 'test_query'}}}
        # )
        assert len(self.mock_es_instance.index.mock_calls) == 7
        result = executed['data']['update_automation_task']['task_result']
        assert result['id'] == self.at_id
        assert result['duration'] == 909
        assert result['metrics'][0]['k'] == "rupture_count"
        assert result['metrics'][0]['v'] == "20"
        assert result['state'] == "DONE"
        assert result['result'] == "SUCCESS"

        # print(dir(self.mock_es_instance.index.mock_calls[-1]))
        # print(self.mock_es_instance.index.mock_calls[-1].kwargs)
        # check final mock call
        assert self.mock_es_instance.index.mock_calls[-1].kwargs['body']['result'] == 'success'
        assert self.mock_es_instance.index.mock_calls[-1].kwargs['body']['state'] == 'done'
        assert self.mock_es_instance.index.mock_calls[-1].kwargs['index'] == 'test'
