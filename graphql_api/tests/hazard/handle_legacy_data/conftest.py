# # import itertools
# import os

# import boto3
# import pytest
# from dotenv import find_dotenv, load_dotenv
# from graphene.test import Client
# from moto import mock_aws

# from graphql_api.config import REGION, S3_BUCKET_NAME
# from graphql_api.dynamodb.models import migrate
# from graphql_api.schema import root_schema


# @pytest.fixture(scope='session', autouse=True)
# def load_env():
#     env_file = find_dotenv('.env.tests')
#     load_dotenv(env_file)


# @pytest.fixture(scope="module")
# def aws_credentials():
#     """Mocked AWS Credentials for moto."""
#     os.unsetenv("AWS_PROFILE")
#     os.unsetenv("PROFILE")
#     os.environ["AWS_ACCESS_KEY_ID"] = "testing"
#     os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
#     os.environ["AWS_SECURITY_TOKEN"] = "testing"
#     os.environ["AWS_SESSION_TOKEN"] = "testing"
#     os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


# @pytest.fixture(scope='module')
# def graphql_client():
#     # ensure data tables exist
#     with mock_aws():
#         migrate()
#         s3 = boto3.resource('s3', region_name=REGION)
#         s3.create_bucket(Bucket=S3_BUCKET_NAME)
#         yield Client(root_schema)
