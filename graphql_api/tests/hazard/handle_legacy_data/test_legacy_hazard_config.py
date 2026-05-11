"""Test to show that legacy data from the PROD datastore is handled OK."""

import pytest
from graphql_relay import to_global_id

import graphql_api.data  # for mocking

from . import fixtures


@pytest.mark.parametrize(
    "db_object, has_modified_config",
    [
        (lambda _0, _1: fixtures.LEGACY_OHS_T3BlbnF1YWtlSGF6YXJkU29sdXRpb246MTIyMzM1, True),
        (lambda _0, _1: fixtures.LEGACY_OHS_T3BlbnF1YWtlSGF6YXJkU29sdXRpb246MTAwODIx, False),
        (lambda _0, _1: fixtures.LEGACY_OHS_T3BlbnF1YWtlSGF6YXJkU29sdXRpb246MTAzMjQ1, True),
        (lambda _0, _1: fixtures.LEGACY_OHS_T3BlbnF1YWtlSGF6YXJkU29sdXRpb246NjkzMjE5OA__, False),
    ],
)
def test_get_openquake_hazard_solution_node(db_object, has_modified_config, graphql_client, monkeypatch):

    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, '_read_object', db_object)

    query = '''
    query get_solution($id: ID!) {
        node(id:$id) {
        __typename
        ... on OpenquakeHazardSolution {
            created
            csv_archive { id, file_name }
            produced_by { id }
            task_type               # new field defaults to UNDEFINED
            modified_config { id }  # legacy field is not returned on all objects    
        }
        }
    }
    '''
    result = graphql_client.execute(query, variable_values=dict(id=to_global_id('OpenquakeHazardSolution', "ANYID")))
    print(result)

    node = result['data']['node']
    assert node['task_type'] == "UNDEFINED"
    assert (node['modified_config'] is not None) == has_modified_config
