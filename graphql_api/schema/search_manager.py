"""
Search Manager
"""
import os
import boto3
import re
import json
import requests
from requests_aws4auth import AWS4Auth


# region = '' # e.g. us-west-1
SERVICE = 'es'

ES_ENDPOINT = os.getenv("ES_ENDPOINT")
ES_INDEX = os.getenv("ES_INDEX")
ES_REGION = os.getenv("ES_REGION")
ES_DOMAIN_NAME = os.getenv("ES_DOMAIN_NAME")

TYPE = '_doc'

class SearchManager():

    def __init__(self):
        credentials = boto3.Session().get_credentials()
        self._awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
            ES_REGION, SERVICE, session_token=credentials.token)
        self._url = ES_ENDPOINT + '/' + ES_INDEX + '/' + TYPE + '/'

    def index_document(self, key, document):
        # Index the document
        headers = { "Content-Type": "application/json" }
        try:
            print("SearchManager.index_document", self._url + key)
            response = requests.put(self._url + key, auth=self._awsauth, json=document, headers=headers)
            print(response.content)
        except (Exception) as err:
            print("ERR SearchManager.index_document ", err)

    def search(self, term):
        headers = {} # "Content-Type": "application/json" }
        try:
            print("SearchManager.search( ", term)
            response = requests.get(ES_ENDPOINT + '/' + ES_INDEX  + '/_search?q=' + term,
                auth=self._awsauth, headers=headers)
            print(response.content)
        except (Exception) as err:
            print("ERR SearchManager.search() ", err)
