from graphql_api.schema.custom import inversion_solution
from typing import Sized

from io import BytesIO
from unittest import mock
from unittest.mock import patch

import datetime as dt
import unittest

from dateutil.tz import tzutc

from graphene.test import Client
from graphql_api import data_s3
from copy import copy

from graphql_api.schema import root_schema
from graphql_relay import from_global_id, to_global_id
from graphql_api.data_s3.file_relation_data import FileRelationData


import graphql_api.data_s3  # for mocking


AUTO_TASK = {
    "id": "6040tkPow",
    "created": "2021-12-20T09:24:59.371931+00:00",
    "files": ["21001AXf9j", "21005LE452", "21008R7VUG"],
    "result": "success",
    "state": "done",
    "duration": 97.022132,
    "parents": ["5820YXyzX"],
    "arguments": None,
    "environment": None,
    "metrics": None,
    "model_type": "crustal",
    "task_type": "inversion",
    "inversion_solution": None,
    "clazz_name": "AutomationTask",
}
FILE_REL0 = {
    "id": "21001AXf9j",
    "thing": None,
    "file": None,
    "role": "read",
    "thing_id": "6040tkPow",
    "file_id": "16742.0Ukmre",
    "clazz_name": "FileRelation",
}
FILE_REL1 = {
    "id": "21005LE452",
    "thing": None,
    "file": None,
    "role": "write",
    "thing_id": "6040tkPow",
    "file_id": "17184.06nh58",
    "clazz_name": "FileRelation",
}
FILE_REL2 = {
    "id": "21008R7VUG",
    "thing": None,
    "file": None,
    "role": "write",
    "thing_id": "6040tkPow",
    "file_id": "17187.0b3Cn3",
    "clazz_name": "FileRelation",
}
FILE0 = {
    "id": "16742.0Ukmre",
    "file_name": "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip",
    "md5_digest": "W4HpdeO/Rn+nOwOgLPko+A==",
    "file_size": 29283271,
    "file_url": None,
    "post_url": None,
    "meta": None,
    "relations": None,
    "created": "2021-12-09T06:41:09.351578+00:00",
    "metrics": [
        {"k": "total_ruptures", "v": "447797"},
        {"k": "perturbed_ruptures", "v": "15575"},
    ],
    "produced_by_id": "QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY",
    "mfd_table_id": None,
    "hazard_table_id": None,
    "tables": None,
    "hazard_table": None,
    "mfd_table": None,
    "produced_by": None,
    "clazz_name": "InversionSolution",
}
FILE1 = {
    "id": "17184.06nh58",
    "file_name": "Wellington_ruptures_radius(200km)_rate_filter(1e-15).geojson",
    "md5_digest": "+bfJDziXGNxQpeX5HpMJKw==",
    "file_size": 725970,
    "file_url": None,
    "post_url": None,
    "meta": None,
    "relations": ["21005LE452"],
    "clazz_name": "File",
}
FILE2 = {
    "id": "17187.0b3Cn3",
    "file_name": "Wellington_ruptures_radius(200km)_rate_filter(1e-15)_sub_solution.zip",
    "md5_digest": "Qdo0ZuxcDzaNZSq9xzTqLA==",
    "file_size": 29144881,
    "file_url": None,
    "post_url": None,
    "meta": None,
    "relations": ["21008R7VUG"],
    "created": "2021-12-20T09:26:17.326242+00:00",
    "metrics": None,
    "mfd_table_id": None,
    "hazard_table_id": None,
    "tables": None,
    "hazard_table": None,
    "mfd_table": None,
    "produced_by": None,
    "clazz_name": "InversionSolution",
}


class TestInversionSolutionRelationBugFix(unittest.TestCase):
    """
        This test replicates a bug which occurs from the relation of two inversion solutions, one as read and one as write
        The automation task inversion solution resolver needs to be able to handle having a read and write solution
        The get_one function is mocked 3 times, as it is called 3 times by the list of file relations in auto task : 
            - "files": ["21001AXf9j", "21005LE452", "21008R7VUG"],
        Each time it is called, the inversion_solution_resolver calls file_relation.get_one(file_id)and checks if it has a 
        'role' of write, if it doesn't it continues. If the 'role' is write, it calls file.get_one(file_relation.file_id) 
        and checks if it is an InversionSolution. 
        mock_get_one is patched for all 3 file_rels which it traverse through and checks if its 'role' is write (FILE_REL1 & FILE_REL2 are).
        Because FILE_REL1 is write, mock_read_object sees if its an InversionSolution (which it is not), and then continues onto 
        FILE_REL2 which is.
        It has now found the correct file relation!
    """
    def setUp(self) -> None:
        self.client = Client(root_schema)
        
    @mock.patch('graphql_api.data_s3.file_relation_data.FileRelationData.get_one',
                side_effect = [FileRelationData.from_json(copy(FILE_REL0)),
                               FileRelationData.from_json(copy(FILE_REL1)), 
                               FileRelationData.from_json(copy(FILE_REL2))])

    @mock.patch('graphql_api.data_s3.BaseDynamoDBData._read_object',
        side_effect = [copy(AUTO_TASK), copy(FILE1), copy(FILE2)])
    def test_query_with_files(self, mocked_read_object, mocked_get_one):
        qry = """ 
        query InversionSolutionDiagnosticContainerQuery {
            nodes(id_in: ["QXV0b21hdGlvblRhc2s6NjA0MHRrUG93"]) {
            result {
                edges {
                node {
                    __typename
                    ... on AutomationTask {
                    created
                    task_type
                    id
                    inversion_solution {
                        id
                        file_name
                        meta {
                        k
                        v
                        }
                        tables {
                        table_id
                        table_type
                        }
                    }
                    }
                }
                }
            }
            }
        }"""

        print(qry)
        executed = self.client.execute(qry)
        print(executed)
        node = executed['data']['nodes']['result']['edges'][0]['node']       
        assert mocked_get_one.call_args[0][0] == "21008R7VUG"
        assert node["inversion_solution"]["id"] == 'SW52ZXJzaW9uU29sdXRpb246MTcxODcuMGIzQ24z'
        assert mocked_read_object.call_count == 3
        assert mocked_get_one.call_count == 3