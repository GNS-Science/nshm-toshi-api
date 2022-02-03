"""
This module exports comfiguration for the current system
"""
import os


def boolean_env(environ_name, default='FALSE'):
    return bool(os.getenv(environ_name, default).upper() in ["1", "Y", "YES", "TRUE"])

IS_OFFLINE = boolean_env('SLS_OFFLINE') #set by serverless-wsgi plugin

if IS_OFFLINE:
    ES_ENDPOINT = "http://localhost:9200"
else:
    ES_ENDPOINT = os.getenv("ES_ENDPOINT", '')


ES_INDEX = os.getenv("ES_INDEX", "toshi-index")
ES_REGION = os.getenv("ES_REGION", 'us-east-1')
ES_DOMAIN_NAME = os.getenv("ES_DOMAIN_NAME")

REGION = os.getenv('REGION', 'us-east-1')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
STACK_NAME = os.getenv('STACK_NAME')
CW_METRICS_RESOLUTION = os.getenv('CW_METRICS_RESOLUTION', 60) #1 for high resolution or 60
