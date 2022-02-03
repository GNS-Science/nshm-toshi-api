"""
This module exports comfiguration for the current system
"""

import os
import enum

class EnvMode(enum.IntEnum):
    AWS = 0
    LOCAL = 1

def boolean_env(environ_name):
    return bool(os.getenv(environ_name, '').upper() in ["1", "Y", "YES", "TRUE"])

#API Setting are needed to sore job details for later reference
IS_OFFLINE = boolean_env('SLS_OFFLINE') #set by serverless-wsgi plugin

if IS_OFFLINE:
    #S3 local credentials
    ES_ENDPOINT = "http://localhost:9200"
else:
    #AWS S3 creds set up by sls
    ES_ENDPOINT = os.getenv("ES_ENDPOINT")

ES_INDEX = os.getenv("ES_INDEX", "toshi-index")
ES_REGION = os.getenv("ES_REGION", 'us-east-1')
ES_DOMAIN_NAME = os.getenv("ES_DOMAIN_NAME")

REGION = os.getenv('REGION', 'us-east-1')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()