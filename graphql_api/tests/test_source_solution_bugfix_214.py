"""
Squash the bug in Scaled and Aggregate Solutinos whene they retrun ther incorrect type for source-solution

"""

from copy import copy

import pytest
from graphene.test import Client
from graphql_relay import to_global_id

import graphql_api.data
from graphql_api.schema import root_schema

scaled_inversion_object_120837 = {
    "id": 120837,
    "file_name": "NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTg4.zip",
    "md5_digest": "TXiN7F4ft1rPzNsKhRgnmQ==",
    "file_size": 27915950,
    "file_url": None,
    "post_url": None,
    # "relations": [{"id": "113188", "role": "write"}, {"id": "113304", "role": "read"}, {"id": "1326904", "role": "read"}, {"id": "1327538", "role": "read"}, {"id": "6529396", "role": "read"}],
    # "predecessors": [{"id": "VGltZURlcGVuZGVudEludmVyc2lvblNvbHV0aW9uOjExOTE2NA==", "depth": -1}, {"id": "SW52ZXJzaW9uU29sdXRpb246MTEzMDYz", "depth": -2}, {"id": "RmlsZToxMDAwODc=", "depth": -3}],
    "meta": [
        {"k": "scale", "v": "1.41"},
        {"k": "polygon_scale", "v": "0.8"},
        {"k": "polygon_max_mag", "v": "8"},
        {"k": "model_type", "v": "CRUSTAL"},
    ],
    "created": "2022-08-12T02:57:05.508741+00:00",
    "metrics": None,
    "mfd_table_id": None,
    "hazard_table_id": None,
    "tables": None,
    "hazard_table": None,
    "mfd_table": None,
    "produced_by": "QXV0b21hdGlvblRhc2s6MTEzMTg4",
    "source_solution": "VGltZURlcGVuZGVudEludmVyc2lvblNvbHV0aW9uOjExOTE2NA==",
    "clazz_name": "ScaledInversionSolution",
}


td_solution_object_119164 = {
    "id": 119164,
    "file_name": "NZSHM22_TimeDependentInversionSolution-QXV0b21hdGlvblRhc2s6MTExNjI5.zip",
    "md5_digest": "iwBRIm0peyP4Ym9p0er0AA==",
    "file_size": 27915865,
    "file_url": None,
    "post_url": None,
    "meta": [
        {"k": "current_year", "v": "2022"},
        {"k": "mre_enum", "v": "CFM_1_1"},
        {"k": "forecast_timespan", "v": "100"},
        {"k": "aperiodicity", "v": "NZSHM22"},
        {"k": "model_type", "v": "CRUSTAL"},
        {
            "k": "file_path",
            "v": "/work/chrisdc/NZSHM-WORKING/PROD/downloads/SW52ZXJzaW9uU29sdXRpb246MTEzMDYz/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTA3MDE2.zip",
        },
    ],
    "relations": [
        {"id": "111629", "role": "write"},
        {"id": "113188", "role": "read"},
        {"id": "113189", "role": "read"},
        {"id": "113191", "role": "read"},
    ],
    "predecessors": [{"id": "SW52ZXJzaW9uU29sdXRpb246MTEzMDYz", "depth": -1}, {"id": "RmlsZToxMDAwODc=", "depth": -2}],
    "created": "2022-08-09T23:37:05.247558+00:00",
    "metrics": None,
    "mfd_table_id": None,
    "hazard_table_id": None,
    "tables": None,
    "hazard_table": None,
    "mfd_table": None,
    "produced_by": "QXV0b21hdGlvblRhc2s6MTExNjI5",
    "source_solution": "SW52ZXJzaW9uU29sdXRpb246MTEzMDYz",
    "clazz_name": "TimeDependentInversionSolution",
}


@pytest.fixture(scope="module")
def graphene_client():
    yield Client(root_schema)


@pytest.fixture
def mock_dynamodb_read(monkeypatch):
    """Requests.get() mocked to return {'mock_key':'mock_response'}."""

    def mock_read(self, *args, **kwargs):
        if args[0] == "119164":
            return copy(td_solution_object_119164)
        elif args[0] == "120837":
            return copy(scaled_inversion_object_120837)
        else:
            raise ValueError(f"{args}, {kwargs}")

    monkeypatch.setattr(graphql_api.data.BaseDynamoDBData, "_read_object", mock_read)


def test_scaled_inversion_example(graphene_client, mock_dynamodb_read):
    """Test fgor modern DynamoDB objects"""
    QRY = """
        query A {
          node(id:"%s") {
            __typename
            ...on ScaledInversionSolution {
              __typename
              id
              source_solution {
                __typename
                ... on Node {
                    id
                }
              }
              predecessors {
                typename
                id
                depth
                relationship
              }
            }
          }
        }
    """ % to_global_id(
        'ScaledInversionSolution', 120837
    )

    result = graphene_client.execute(QRY)
    print(result)
    # assert mocked_api.call_count == 2
    assert result['data']['node']['source_solution']['id'] == "VGltZURlcGVuZGVudEludmVyc2lvblNvbHV0aW9uOjExOTE2NA=="
    assert result['data']['node']['source_solution']['__typename'] == "TimeDependentInversionSolution"
