"""Test demonstrationg that we can cast old file data into RuptureSet objects when appropriate."""

import pytest
from graphql_relay import from_global_id, to_global_id

import graphql_api.data  # for mocking
import graphql_api.data.file_data  # for mocking

from . import fixtures


@pytest.fixture()
def query():
    yield '''
    query get_file_or_ruptset($id: ID!) {
        node(id:$id) {
            __typename
            ... on File {
                file_name
                file_size
                md5_digest
                file_url
            }
            ... on RuptureSet {
                created
                file_name
                file_size
                md5_digest
                file_url
                fault_models
                relations {
                    total_count
                }
            }
        }
    }
    '''


# Shared test parameters: "db_object, fault_models"
LEGACY_FILES = [
    (lambda _0, _1: fixtures.LEGACY_FILE_RmlsZToyNjI2MC4wZlRkTVQ_eq, ["CFM_1_0_DOM_SANSTVZ"]),
    (lambda _0, _1: fixtures.LEGACY_FILE_RmlsZTo3MTQ3LjVramh3Rg_eq_eq, ["SBD_0_3_HKR_LR_30"]),
    (lambda _0, _1: fixtures.LEGACY_FILE_RmlsZToxMjkwOTg0, ["SBD_0_2_PUY_15"]),
]


@pytest.mark.parametrize("db_object, fault_models", LEGACY_FILES)
def test_legacy_file_as_file(db_object, fault_models, query, graphql_client, monkeypatch):

    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, '_read_object', db_object)
    monkeypatch.setattr(graphql_api.data.file_data, 'MIGRATE_FILE_TO_RUPTSET', False)

    expected_data = db_object(None, None)
    result = graphql_client.execute(query, variable_values=dict(id=to_global_id('File', expected_data['id'])))
    print(result)
    assert result['data']['node']['__typename'] == "File"
    assert result['data']['node']['file_name'] == expected_data['file_name']
    assert result['data']['node']['file_size'] == expected_data['file_size']
    assert result['data']['node']['md5_digest'] == expected_data['md5_digest']
    assert result['data']['node']['file_url'] is not None


@pytest.mark.parametrize("db_object, fault_models", LEGACY_FILES)
def test_legacy_file_as_RuptureSet(db_object, fault_models, query, graphql_client, monkeypatch):
    # help us set up fixtures ....
    print(from_global_id("RmlsZToyNjI2MC4wZlRkTVQ="))
    print(from_global_id("RmlsZTo3MTQ3LjVramh3Rg=="))

    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, '_read_object', db_object)
    monkeypatch.setattr(graphql_api.data.file_data, 'MIGRATE_FILE_TO_RUPTSET', True)

    expected_data = db_object(None, None)
    result = graphql_client.execute(query, variable_values=dict(id=to_global_id('File', expected_data['id'])))
    print(result)
    assert result['data']['node']['__typename'] == "RuptureSet"
    assert result['data']['node']['file_name'] == expected_data['file_name']
    assert result['data']['node']['file_size'] == expected_data['file_size']
    assert result['data']['node']['md5_digest'] == expected_data['md5_digest']
    assert result['data']['node']['created'] == expected_data.get('created')
    assert result['data']['node']['file_url'] is not None
    assert result['data']['node']['fault_models'] == fault_models
    assert result['data']['node']['relations']['total_count'] == len(expected_data['relations'])
