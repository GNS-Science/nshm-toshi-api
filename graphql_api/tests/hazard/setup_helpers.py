"""
A Mixin class to share in test modules

The TestCase sub class must setup self.client

"""

import base64
import datetime as dt
from hashlib import sha256
from io import BytesIO

from dateutil.tz import tzutc


def fake_file_content():
    filedata = BytesIO("not_really zip, but close enough".encode())
    filedata.seek(0)  # important!
    return filedata


def file_size(fileobj):
    size = len(fileobj.read())
    fileobj.seek(0)
    return size


def file_digest(fileobj):
    digest = sha256(fileobj.read()).hexdigest()
    fileobj.seek(0)
    return digest


class SetupHelpersMixin:
    def create_general_task(self):
        CREATE_QRY = '''
            mutation {
              create_general_task(input: {
                  agent_name:"XOXO"
                  title:"The title"
                  description:"a description"
                  created: "2021-08-03T01:38:21.933731+00:00"
                  argument_lists: {k: "some_metric", v: ["20", "25"]}
              })
              {
                  general_task {
                    id
                    created
                  }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY)
        print(result)
        return result['data']['create_general_task']['general_task']['id']

    def create_source_solution(self):
        CREATE_QRY = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!, $produced_by: ID!) {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by: $produced_by
                  metrics: [{k: "some_metric", v: "20"}]
                  created: "2021-06-11T02:37:26.009506Z"
                  }
              ) {
              inversion_solution { id }
              }
            }
        '''

        result = self.client.execute(
            CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID"),
        )

        print(result)
        return result['data']['create_inversion_solution']['inversion_solution']['id']

    def create_automation_task(self, task_type="INVERSION"):
        CREATE_QRY = '''
            mutation ($created: DateTime! $task_type: TaskSubType!) {
                create_automation_task(input: {
                    task_type: $task_type
                    state: STARTED
                    result: UNDEFINED
                    created: $created
                    duration: 600

                    arguments: [
                        { k:"rates_scalar" v: "0.5" }
                    ]

                    }
                    )
                    {
                        task_result {
                        id
                        task_type
                        created
                        duration
                        arguments {k v}
                    }
                }
            }
        '''
        result = self.client.execute(
            CREATE_QRY,
            variable_values=dict(
                task_type=task_type,
                created="2021-06-11T02:37:26.009506Z",
                file_name='MyInversion.zip',
                file_size=1000,
                produced_by="PRODUCER_ID",
            ),
        )

        print(result)
        return result['data']['create_automation_task']['task_result']['id']

    def create_gt_relation(self, parent_id, child_id):
        CREATE_QRY = '''
            mutation new_gt_link ($parent_id: ID!, $child_id: ID!) {
              create_task_relation(
                parent_id: $parent_id
                child_id: $child_id
              )
              {
                ok
                thing_relation { child_id }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY, variable_values=dict(parent_id=parent_id, child_id=child_id))
        print(result)
        return result['data']['create_task_relation']['thing_relation']

    def create_inversion_solution_nrml(self, upstream_sid):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $digest: String!, $file_name: String!, $file_size: BigInt!, $created: DateTime!) {
              create_inversion_solution_nrml(
                  input: {
                      source_solution: $source_solution
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                  }
              )
              {
                ok
                inversion_solution_nrml { id, file_name, file_size, md5_digest, post_url, 
                source_solution { ... on Node { id } }}
              }
            }'''

        fake_file = fake_file_content()
        variables = dict(
            source_solution=upstream_sid,
            file=fake_file,
            digest=file_digest(fake_file),
            file_name="alineortwo.zip",
            file_size=file_size(fake_file),
            created=dt.datetime.utcnow().isoformat(),
        )
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_inversion_solution_nrml_with_predecessors(self, upstream_sid):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $digest: String!, $file_name: String!, $file_size: BigInt!, $created: DateTime!
                $predecessors: [PredecessorInput]) {
              create_inversion_solution_nrml(
                  input: {
                      source_solution: $source_solution
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                      predecessors: $predecessors
                  }
              )
              {
                ok
                inversion_solution_nrml { id, file_name, file_size, md5_digest, post_url,
                    source_solution { ... on Node{ id } }
                    predecessors {
                        id,
                        typename,
                        depth,
                        relationship
                        node {
                            ... on FileInterface {
                                meta {k v}
                                file_name
                            }
                        }
                    }
                }
              }
            }'''

        fake_file = fake_file_content()

        predecessors = [dict(id=upstream_sid, depth=-1)]

        variables = dict(
            source_solution=upstream_sid,
            file=fake_file,
            digest=file_digest(fake_file),
            file_name="alineortwo.zip",
            file_size=file_size(fake_file),
            created=dt.datetime.utcnow().isoformat(),
            predecessors=predecessors,
        )

        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_file(self, filename, predecessor=None):
        """test helper"""
        query = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!, $predecessors: [PredecessorInput]) {
              create_file(
                    md5_digest:$digest
                    file_name: $file_name
                    file_size: $file_size
                    predecessors: $predecessors
                ) {
                    ok
                    file_result {
                        id, file_name, file_size, md5_digest, post_url
                        predecessors {
                            id,
                            typename,
                            depth,
                            relationship
                            node {
                                ... on FileInterface {
                                    meta {k v}
                                    file_name
                                }
                            }
                        }
                    }
                }
            }
        '''

        fake_file = fake_file_content()

        variables = dict(
            file=fake_file,
            digest=file_digest(fake_file),
            file_name=filename,
            file_size=file_size(fake_file),
            created=dt.datetime.now(tzutc()).isoformat(),
        )

        if predecessor:
            predecessors = [dict(id=predecessor, depth=-1)]
            variables['predecessors'] = predecessors

        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_openquake_config(self, sources, archive_id):
        """test helper"""
        query = '''
            mutation ($created: DateTime!, $sources: [ID!], $archive_id: ID!) {
              create_openquake_hazard_config(
                  input: {
                      created: $created
                      source_models: $sources
                      template_archive: $archive_id
                  }
              )
              {
                ok
                config {
                    id
                    created
                    source_models { ... on Node{ id } }
                }
              }
            }'''

        variables = dict(sources=sources, archive_id=archive_id, created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def build_hazard_task(self, disagg=False):
        if not disagg:
            return self.create_openquake_hazard_task()  # Thing 100001

        return self.create_openquake_hazard_disagg_task()

    def create_openquake_hazard_task(self, config=None):
        """test helper"""
        query = '''
            mutation ($created: DateTime!, $config: ID) {
              create_openquake_hazard_task(
                  input: {
                    config: $config
                    created: $created
                    model_type: COMPOSITE
                    state: UNDEFINED
                    result: UNDEFINED

                    arguments: [
                        { k:"max_jump_distance" v: "55.5" }
                        { k:"max_sub_section_length" v: "2" }
                        { k:"max_cumulative_azimuth" v: "590" }
                        { k:"min_sub_sections_per_parent" v: "2" }
                        { k:"permutation_strategy" v: "DOWNDIP" }
                    ]

                    environment: [
                        { k:"gitref_opensha_ucerf3" v: "ABC"}
                        { k:"gitref_opensha_commons" v: "ABC"}
                        { k:"gitref_opensha_core" v: "ABC"}
                        { k:"nshm_nz_opensha" v: "ABC"}
                        { k:"host" v:"tryharder-ubuntu"}
                        { k:"JAVA" v:"-Xmx24G"  }
                    ]
                  }
              )
              {
                ok
                openquake_hazard_task { id, config { id }, created, arguments {k v}}
              }
            }'''

        variables = dict(config=config, created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables)
        print(result)
        ht_id = result['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']
        # this shows the id to be used with ToshiThingObject.get()
        print(base64.b64decode(ht_id).decode("ascii"))
        return result

    def create_openquake_hazard_disagg_task(self):
        """test helper"""
        query = '''
            mutation ($created: DateTime!) {
              create_openquake_hazard_task(
                  input: {
                    created: $created
                    model_type: COMPOSITE
                    task_type: DISAGG
                    state: UNDEFINED
                    result: UNDEFINED

                    arguments: [
                        { k:"max_jump_distance" v: "55.5" }
                        { k:"max_sub_section_length" v: "2" }
                        { k:"max_cumulative_azimuth" v: "590" }
                        { k:"min_sub_sections_per_parent" v: "2" }
                        { k:"permutation_strategy" v: "DOWNDIP" }
                    ]

                    environment: [
                        { k:"gitref_opensha_ucerf3" v: "ABC"}
                        { k:"gitref_opensha_commons" v: "ABC"}
                        { k:"gitref_opensha_core" v: "ABC"}
                        { k:"nshm_nz_opensha" v: "ABC"}
                        { k:"host" v:"tryharder-ubuntu"}
                        { k:"JAVA" v:"-Xmx24G"  }
                    ]
                  }
              )
              {
                ok
                openquake_hazard_task { id, created, arguments {k v}}
              }
            }'''

        variables = dict(created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables)
        print(result)
        ht_id = result['data']['create_openquake_hazard_task']['openquake_hazard_task']['id']
        # this shows the id to be used with ToshiThingObject.get()
        print(base64.b64decode(ht_id).decode("ascii"))
        return result

    def create_scaled_solution(self, upstream_sid, task_id):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $produced_by: ID!, $digest: String!, $file_name: String!, $file_size: BigInt!, $created: DateTime!) {
              create_scaled_inversion_solution(
                  input: {
                      source_solution: $source_solution
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                      produced_by: $produced_by
                  }
              )
              {
                ok
                solution { id, file_name, file_size, md5_digest, post_url, 
                    source_solution { ... on Node{id} }
                    produced_by { ... on Node{ id } }
                }
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!
        variables = dict(
            source_solution=upstream_sid,
            produced_by=task_id,
            file=filedata,
            digest=digest,
            file_name="alineortwo.txt",
            file_size=size,
        )
        variables['created'] = dt.datetime.now(tzutc()).isoformat()
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_time_dependent_solution(self, upstream_sid, task_id):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $produced_by: ID!, $digest: String!, $file_name: String!, $file_size: BigInt!, $created: DateTime!) {
              create_time_dependent_inversion_solution(
                  input: {
                      source_solution: $source_solution
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                      produced_by: $produced_by
                  }
              )
              {
                ok
                solution { id, file_name, file_size, md5_digest, post_url,
                    source_solution { ... on Node{id} }
                    produced_by { ... on Node{ id } }
                }
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!
        variables = dict(
            source_solution=upstream_sid,
            produced_by=task_id,
            file=filedata,
            digest=digest,
            file_name="alineortwo.txt",
            file_size=size,
        )
        variables['created'] = dt.datetime.now(tzutc()).isoformat()
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_aggregate_solution(self, upstream_sids, task_id, aggregation_fn, common_rupture_set):
        """test helper"""
        query = '''
            mutation ($source_solutions: [ID]!, $produced_by: ID!, $digest: String!,
                $file_name: String!, $file_size: BigInt!, $created: DateTime!,
                $aggregation_fn: AggregationFn!, $common_rupture_set: ID!) {
              create_aggregate_inversion_solution(
                  input: {
                      source_solutions: $source_solutions
                      aggregation_fn: $aggregation_fn
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                      produced_by: $produced_by
                      common_rupture_set: $common_rupture_set
                  }
              )
              {
                ok
                solution { id, file_name, file_size, md5_digest, post_url, 
                    source_solutions { ... on Node{id} }
                    produced_by { ... on Node{id} }
                    common_rupture_set { id }
                }
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!
        variables = dict(
            source_solutions=upstream_sids,
            produced_by=task_id,
            file=filedata,
            digest=digest,
            file_name="alineortwo.txt",
            file_size=size,
            aggregation_fn=aggregation_fn,
            common_rupture_set=common_rupture_set,
        )
        variables['created'] = dt.datetime.now(tzutc()).isoformat()
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result

    def create_aggregate_solution_with_predecessors(self, source_solutions, task_id, common_rupture_set):
        """test helper"""
        query = '''
           mutation ($source_solutions: [ID]!, $produced_by: ID!, $digest: String!,
                $file_name: String!, $file_size: BigInt!, $created: DateTime!,
                $predecessors: [PredecessorInput], $common_rupture_set: ID!) {
              create_aggregate_inversion_solution(
                  input: {
                      source_solutions: $source_solutions
                      aggregation_fn: MEAN
                      md5_digest: $digest
                      file_name: $file_name
                      file_size: $file_size
                      created: $created
                      produced_by: $produced_by
                      predecessors: $predecessors
                      common_rupture_set: $common_rupture_set
                    })
              {
                ok
                solution { id, file_name, file_size, md5_digest, post_url
                    source_solutions { ... on Node{id} }
                    produced_by { ... on Node{id} }
                    predecessors {
                        id,
                        typename,
                        depth,
                        relationship
                        node {
                            ... on FileInterface {
                                meta {k v}
                                file_name
                            }
                        }
                    }
                }
              }
            }'''

        # from hashlib import sha256, md5
        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!

        predecessors = [dict(id=source_solutions[0], depth=-1)]

        variables = dict(
            source_solutions=source_solutions,
            produced_by=task_id,
            file=filedata,
            digest=digest,
            file_name="alineortwo.txt",
            file_size=size,
            predecessors=predecessors,
            common_rupture_set=common_rupture_set,
        )
        variables['created'] = dt.datetime.now(tzutc()).isoformat()
        result = self.client.execute(query, variable_values=variables)
        print(result)
        return result
