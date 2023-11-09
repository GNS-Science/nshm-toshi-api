"""
Search Manager
"""
import logging
from datetime import datetime as dt

import requests

from graphql_api.cloudwatch import ServerlessMetricWriter
from graphql_api.config import CW_METRICS_RESOLUTION, STACK_NAME
from graphql_api.data.file_data import FileData
from graphql_api.data.table_data import TableData
from graphql_api.data.thing_data import ThingData

logger = logging.getLogger(__name__)

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

TYPE = '_doc'
ES_CONNECT_TIMEOUT = 2  # connection timeout seconds
ES_READ_TIMEOUT = 5  # response timeout seconds


class SearchManager:
    def __init__(self, endpoint, es_index, awsauth):
        self._awsauth = awsauth
        self._endpoint = endpoint
        self._es_index = es_index
        self._url = endpoint + '/' + es_index + '/' + TYPE + '/'

    def index_document(self, key, document):
        # Index the document
        t0 = dt.utcnow()
        es_key = key.replace("/", "_")
        headers = {"Content-Type": "application/json"}
        try:
            logger.debug(f"SearchManager.index_document {self._url + es_key}")
            response = requests.put(
                self._url + es_key,
                auth=self._awsauth,
                json=document,
                headers=headers,
                timeout=(ES_CONNECT_TIMEOUT, ES_READ_TIMEOUT),
            )
            logger.debug(f'index_document response: {response.content}')
        except Exception as err:
            logger.warning(f'index_document raised err: {err}')
        db_metrics.put_duration(__name__, 'index_document', dt.utcnow() - t0)

    def search(self, term):
        t0 = dt.utcnow()

        headers = {}  # "Content-Type": "application/json" }
        result = []
        try:
            logger.debug(f"SearchManager.search({term})")
            qurl = self._endpoint + '/' + self._es_index + '/_search?q=' + term
            logger.debug(f"Query URL: {qurl}")
            response = requests.get(qurl, auth=self._awsauth, headers=headers).json()
            # print(response)
            # count = response['hits']['total']
            # print ("count",  count)
            for obj in response['hits']['hits']:
                logger.debug(f"hit: {(obj['_index'], obj['_type'], obj['_id'], obj['_score'])}")
                # if 'TaskData' in obj['_id']:
                #     result.append(RuptureGenerationTask.from_json(obj['_source']))
                # el
                if 'FileData' in obj['_id']:
                    result.append(FileData.from_json(obj['_source']))
                elif 'ThingData' in obj['_id']:
                    # clazz_name = obj['_source'].pop('clazz_name')
                    # clazz = getattr(import_module('graphql_api.schema'), clazz_name)
                    logger.info("search got object ")
                    result.append(ThingData.from_json(obj['_source']))
                elif 'TableData' in obj['_id']:
                    result.append(TableData.from_json(obj['_source']))
                else:
                    raise ValueError("unable to resolve, object id", obj['_source'])

        except Exception as err:
            logger.warning(f"search() raised err: {err}")

        db_metrics.put_duration(__name__, 'search', dt.utcnow() - t0)
        return result
