# import itertools
import os

import pytest
from dotenv import find_dotenv, load_dotenv
from graphene.test import Client
from moto import mock_aws

from graphql_api.dynamodb.models import migrate
from graphql_api.schema import root_schema


@pytest.fixture(scope='session', autouse=True)
def load_env():
    env_file = find_dotenv('.env.tests')
    load_dotenv(env_file)


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.unsetenv("AWS_PROFILE")
    os.unsetenv("PROFILE")
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope='module')
def graphql_client():
    # ensure data tables exist
    with mock_aws():
        migrate()
        yield Client(root_schema)


@pytest.fixture(scope='session')
def create_gt_mutation():
    yield '''
    mutation new_gt ($created: DateTime!) {
      create_general_task(input:{
        created: $created
        title: "TEST Build opensha rupture set Coulomb #1"
        description:"Using "
        agent_name:"chrisbc"
        subtask_type: OPENQUAKE_HAZARD,
        model_type: COMPOSITE
        argument_lists: [
            {k: "some_metric", v: ["20", "25"]},
            {k: "swept", v: ["A", "B", "C"]}
            ]
      })
      {
        general_task{
          id
          subtask_type
          model_type
        }
      }
    }
'''


@pytest.fixture(scope='session')
def create_at_mutation():
    yield '''
    mutation ($created: DateTime!, $gt_id: ID!) {
        create_automation_task(input: {
            general_task_id: $gt_id
            task_type: INVERSION
            state: UNDEFINED
            result: UNDEFINED
            created: $created
            duration: 600

            arguments: [
                { k:"max_jump_distance" v: "55.5" }
            ]

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

            ##EXTRA_INPUT##

            }
            )
            {
                task_result {
                id
                general_task_id
                arguments {k v}
                task_type
            }
        }
    }
'''
