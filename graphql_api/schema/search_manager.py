"""
Search Manager
"""
import requests
from graphql_api.data.thing_data import ThingData
from graphql_api.data.file_data import FileData
from graphql_api.data.table_data import TableData

from datetime import datetime as dt
from graphql_api.config import STACK_NAME, CW_METRICS_RESOLUTION
from graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION)

TYPE = '_doc'

class SearchManager():

    def __init__(self, endpoint, es_index, awsauth):
        self._awsauth = awsauth
        self._endpoint = endpoint
        self._es_index = es_index
        self._url = endpoint + '/' + es_index + '/' + TYPE + '/'

    def index_document(self, key, document):
        # Index the document
        t0 = dt.utcnow()
        headers = { "Content-Type": "application/json" }
        try:
            # print("SearchManager.index_document", self._url + key)
            # print('DOCUMENT:', document)
            response = requests.put(self._url + key, auth=self._awsauth, json=document, headers=headers)
            print(response.content)
        except (Exception) as err:
            print("ERR SearchManager.index_document ", err)
        db_metrics.put_duration(__name__, 'index_document' , dt.utcnow()-t0)

    def search(self, term):
        t0 = dt.utcnow()

        headers = {} # "Content-Type": "application/json" }
        result = []
        try:
            #print("SearchManager.search( ", term)
            qurl = self._endpoint + '/' + self._es_index  + '/_search?q=' + term
            print("Query URL: ", qurl)
            response = requests.get(qurl, auth=self._awsauth, headers=headers).json()
            # print(response)
            #count = response['hits']['total']
            #print ("count",  count)
            for obj in response['hits']['hits']:
                print( obj['_index'], obj['_type'], obj['_id'], obj['_score'])
                # if 'TaskData' in obj['_id']:
                #     result.append(RuptureGenerationTask.from_json(obj['_source']))
                # el
                if 'FileData' in obj['_id']:
                    result.append(FileData.from_json(obj['_source']))
                elif 'ThingData' in obj['_id']:
                    # clazz_name = obj['_source'].pop('clazz_name')
                    # clazz = getattr(import_module('graphql_api.schema'), clazz_name)
                    result.append(ThingData.from_json(obj['_source']))
                elif 'TableData' in obj['_id']:
                    result.append(TableData.from_json(obj['_source']))
                else:
                    raise ValueError("unable to resolve, object id", obj['_source'])

        except (Exception) as err:
            print("ERR SearchManager.search() ", err)

        db_metrics.put_duration(__name__, 'index_document' , dt.utcnow()-t0)
        return result