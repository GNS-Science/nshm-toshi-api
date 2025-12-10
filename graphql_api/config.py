"""
This module exports comfiguration for the current system
"""

import os

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env


def boolean_env(environ_name, default='FALSE'):
    return bool(os.getenv(environ_name, default).upper() in ["1", "Y", "YES", "TRUE"])


IS_OFFLINE = boolean_env('SLS_OFFLINE')  # set by serverless-wsgi plugin
TESTING = boolean_env('TESTING')
DB_READ_ONLY = boolean_env( # use this if you want to test without fear of accidental writing to datastore.
    'DB_READ_ONLY'
)  
CLOUDWATCH_ENABLED = boolean_env('CLOUDWATCH_ENABLED', 'yes')

# Switch to control dynamic migrations of legacy `File` to `RuptureSet`
MIGRATE_FILE_TO_RUPTSET = boolean_env('MIGRATE_FILE_TO_RUPTSET', 'no')

if IS_OFFLINE:
    ES_ENDPOINT = "http://localhost:9200"
    DB_ENDPOINT = "http://localhost:8000"
else:
    ES_ENDPOINT = os.getenv("ES_ENDPOINT", '')
    DB_ENDPOINT = os.getenv("DB_ENDPOINT", '')

ES_INDEX = os.getenv("ES_INDEX", "toshi-index-mapped")
ES_REGION = os.getenv("ES_REGION", 'us-east-1')
ES_DOMAIN_NAME = os.getenv("ES_DOMAIN_NAME")

REGION = os.getenv('REGION', 'us-east-1')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
STACK_NAME = os.getenv('STACK_NAME')
CW_METRICS_RESOLUTION = os.getenv('CW_METRICS_RESOLUTION', 60)  # 1 for high resolution or 60
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', "S3_BUCKET_NAME_unconfigured")
FIRST_DYNAMO_ID = int(os.getenv('FIRST_DYNAMO_ID', 100000))

LOGGING_CFG = os.getenv('LOGGING_CFG', 'graphql_api/logging_aws.yaml')
