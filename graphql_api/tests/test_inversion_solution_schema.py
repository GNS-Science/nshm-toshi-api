
"""
Test API function for InversionSolution
Mocking our data layer

"""
from io import BytesIO
from unittest import mock

import datetime as dt
import unittest
import json

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data

from graphql_api.schema import root_schema
from graphql_api.schema.custom.inversion_solution import InversionSolution, CreateInversionSolution

import graphql_api.data # for mocking

class IncrId():
    next_id = -1

    def get_next_id(self, *args):
        self.next_id +=1
        return str(self.next_id) + 'RANDM'

READ_MOCK = lambda _self, id: dict(
    id = "0i93qK",
    clazz_name = "InversionSolution",
    md5_digest = "$digest",
    file_name = "$file_name",
    file_size = "$file_size",
    produced_by_id = "VGFibGU6Tm9uZQ==",
    mfd_table_id = "VGFibGU6MA==",
    created = "2021-06-11T02:37:26.009506+00:00",
    meta = [{ "k":"max_jump_distance", "v": "55.5" }],
    metrics = [{ "k":"some_metric", "v": "20"}],
    tables = [{'identity':'table0',
      "created": "2021-06-11T02:37:26.009506+00:00",
      "produced_by_id": "VGFibGU6Tm9uZQ==",
      "label":"MyMFDTable",
      "table_id": "VGFibGU6MA==",
      "dimensions": [{"k": "grid_spacings", "v": ["0.1"]}, {"k": "IML_periods", "v": ["0, 0.1, etc"]},
                 {"k": "tags", "v": ["opensha", "testing"]}, {"k": "gmpes", "v": ["ASK_2014"]}],
      "table_type": "hazard_gridded",
      }]
    )

@mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', IncrId().get_next_id)
@mock.patch('graphql_api.data.file_data.FileData.create', lambda self, clazz_name, **kwargs: {})
#TODO: replace above with this deeper test ....
# @mock.patch('graphql_api.data.BaseS3Data._write_object', lambda self, id, updated_body, **kwargs: {})
class TestBasicInversionSolutionOperations(unittest.TestCase):
    """
    All datastore (data) methods are mocked.
    """
    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseData._read_object', READ_MOCK)
    def test_create_bare_table(self):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $produced_by: ID!, $mfd_table: ID!) {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by_id: $produced_by
                  mfd_table_id: $mfd_table
                  metrics: [{k: "some_metric", v: "20"}]
                  created: "2021-06-11T02:37:26.009506Z"
                  }
              ) {
              inversion_solution { id }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID", mfd_table="TABLE_ID"))
        print(result)
        assert result['data']['create_inversion_solution']['inversion_solution']['id'] == 'SW52ZXJzaW9uU29sdXRpb246Tm9uZQ=='

    @mock.patch('graphql_api.data.BaseData._read_object', READ_MOCK)
    def test_get_inversion_solution_by_node_id(self):
        # the first GT
        qry = '''
        query get_FDT {
          node(id:"VGFibGU6MA==") {
            __typename
            ... on InversionSolution {
              created
              id
              file_name
              mfd_table {
                id
              }
              metrics {k v}
              tables { identity, table_id}
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'SW52ZXJzaW9uU29sdXRpb246MGk5M3FL'
        assert result['data']['node']['file_name'] == "$file_name"
        assert result['data']['node']['mfd_table']['id'] == "VGFibGU6MA=="
        assert result['data']['node']['metrics'][0]['k'] == "some_metric"
        assert result['data']['node']['metrics'][0]['v'] == "20"
        assert result['data']['node']['tables'][0]['identity'] == "table0"


    @mock.patch('graphql_api.data.BaseData._read_object', READ_MOCK)
    @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, id, updated_body, **kwargs: {})
    @mock.patch('graphql_api.data.BaseDynamoDBData.transact_update', lambda self, object_id, object_type, body: None)
    def test_append_inversion_solution_tables(self):
        # the first GT
        qry = '''
        mutation ($input: AppendInversionSolutionTablesInput!) {
          append_inversion_solution_tables(input: $input)
           {
           ok
           inversion_solution {
              id,
              tables {
                identity
                table_id
                table_type
                dimensions {k v}
                table {
                 id
                }
              }
            }
          }
        }
        '''

        input = dict(
            id = "SW52ZXJzaW9uU29sdXRpb246MGk5M3FL",
            tables = [{
              "produced_by_id":"PRODUCER_ID",
              "label": "MyLabelledTable",
              "table_id": "VGFibGU6MA==",
              "table_type" : "HAZARD_GRIDDED",
              "dimensions": [{"k": "grid_spacings", "v": ["0.1"]}, {"k": "IML_periods", "v": ["0", "0.1"]},
                {"k": "tags", "v": ["opensha", 'testing']}, {"k": "gmpes", "v": ["ASK_2014"]}]
            }])

        result = self.client.execute(qry, variable_values=dict(input=input))
        print(result)
        assert result['data']['append_inversion_solution_tables']['inversion_solution']['id'] == 'SW52ZXJzaW9uU29sdXRpb246MGk5M3FL'
        assert len(result['data']['append_inversion_solution_tables']['inversion_solution']['tables']) == 2
        assert result['data']['append_inversion_solution_tables']['inversion_solution']['tables'][1]['table_id'] == "VGFibGU6MA=="
        assert result['data']['append_inversion_solution_tables']['inversion_solution']['tables'][1]['table_type'] == "HAZARD_GRIDDED"
        assert result['data']['append_inversion_solution_tables']['inversion_solution']['tables'][1]['dimensions'][0]['k'] == 'grid_spacings'
        assert result['data']['append_inversion_solution_tables']['inversion_solution']['tables'][1]['table']['id'] == "VGFibGU6MA=="


ISMOCK = lambda _self, id: json.loads('''{
"id": "1544.0vP8Bd",
"file_name": "NZSHM22_InversionSolution-UnVwdHVyZUdlbmVyYXRpb25UYXNrOjcwOXpnTDg5.zip",
"md5_digest": "8tEaawtixFVlzm4iseWeQA==",
"file_size": 2950845,
"file_url": null,
"post_url": null,
"meta": [{"k": "round", "v": "0"}, {"k": "config_type", "v": "crustal"}, {"k": "rupture_set_file_id", "v": "RmlsZToxMzY1LjBzZzRDeA=="}, {"k": "rupture_set", "v": "/tmp/NZSHM/downloads/RmlsZToxMzY1LjBzZzRDeA==/RupSet_Cl_FM(CFM_0_3_SANSTVZ)_noInP(T)_slRtP(0.05)_slInL(F)_cfFr(0.75)_cfRN(2)_cfRTh(0.5)_cfRP(0.01)_fvJm(T)_jmPTh(0.001)_cmRkTh(360)_mxJmD(15)_plCn(T)_adMnD(6)_adScFr(0)_bi(F)_stGrSp(2)_coFr(0.5).zip"}, {"k": "completion_energy", "v": "0.0"}, {"k": "max_inversion_time", "v": "0.25"}, {"k": "mfd_equality_weight", "v": "100.0"}, {"k": "mfd_inequality_weight", "v": "100.0"}, {"k": "slip_rate_weighting_type", "v": "BOTH"}, {"k": "slip_rate_weight", "v": "None"}, {"k": "slip_uncertainty_scaling_factor", "v": "None"}, {"k": "slip_rate_normalized_weight", "v": "1"}, {"k": "slip_rate_unnormalized_weight", "v": "1"}, {"k": "seismogenic_min_mag", "v": "6.8"}],
"relations": ["1735iadkQ"],
"created": "2021-07-17T04:12:47.122510+00:00",
"metrics": [{"k": "total_perturbations", "v": "1889"}, {"k": "total_ruptures", "v": "51147"}, {"k": "perturbed_ruptures", "v": "1140"}, {"k": "final_energy_mfd_inequality", "v": "1.1911481851711869E-4"}, {"k": "ruptures_above_water_level_ratio", "v": "0.0222886972842982"}, {"k": "final_energy_slip_rate", "v": "516.6160888671875"}, {"k": "final_energy_mfd_equality", "v": "130035.234375"}, {"k": "avg_perturbs_per_pertubed_rupture", "v": "1.657017543859649"}, {"k": "final_energy_rupture_rate_minimization", "v": "495.511474609375"}],
"produced_by_id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjcwOXpnTDg5",
"mfd_table_id": "VGFibGU6MG8zZmtm",
"hazard_table_id": null,
"hazard_table": null,
"mfd_table": null,
"produced_by": null,
"tables": [{"identity":"table0", "created": "2021-06-11T02:37:26.009506+00:00", "produced_by_id": "VGFibGU6Tm9uZQ==", "label":"MyMFDTable", "table_id": "VGFibGU6MA=="}],
"clazz_name": "InversionSolution"}''')

class TestCustomResolvers(unittest.TestCase):

    def setUp(self):
        self.client = Client(root_schema)

    @mock.patch('graphql_api.data.BaseData._read_object', ISMOCK)
    def test_get_inversion_solution_resolved_by_id_fields(self):
        # the first GT
        qry = '''
        query {
          node(id:"SW52ZXJzaW9uU29sdXRpb246MTU0NC4wdlA4QmQ=")
          {
            ... on InversionSolution {
              id
              produced_by_id
              produced_by {
                id
              }
              mfd_table_id
              mfd_table {
                id
              }
              hazard_table_id
              hazard_table {
                id
              }
              tables {
                table {
                 id
                }
              }
            }
          }
        }
        '''
        result = self.client.execute(qry, variable_values={})
        print(result)
        assert result['data']['node']['id'] == 'SW52ZXJzaW9uU29sdXRpb246MTU0NC4wdlA4QmQ='
        assert result['data']['node']['produced_by_id'] == "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjcwOXpnTDg5"
        assert result['data']['node']['produced_by']['id'] == "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjcwOXpnTDg5"
        assert result['data']['node']['mfd_table_id'] == 'VGFibGU6MG8zZmtm'
        assert result['data']['node']['mfd_table']['id'] == 'VGFibGU6MG8zZmtm'
        assert result['data']['node']['hazard_table_id'] == None
        assert result['data']['node']['hazard_table'] == None
        assert result['data']['node']['tables'][0]['table']['id'] == "VGFibGU6MA=="
