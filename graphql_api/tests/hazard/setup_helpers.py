"""
A Mixin class to share in test modules

The TestCase sub class must setup self.client

"""
from io import BytesIO
from hashlib import sha256
import datetime as dt
from dateutil.tz import tzutc

def fake_file_content():
    filedata = BytesIO("not_really zip, but close enough".encode())
    filedata.seek(0) #important!
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
            mutation ($digest: String!, $file_name: String!, $file_size: Int!, $produced_by: ID!) {
              create_inversion_solution(input: {
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by_id: $produced_by
                  metrics: [{k: "some_metric", v: "20"}]
                  created: "2021-06-11T02:37:26.009506Z"
                  }
              ) {
              inversion_solution { id }
              }
            }
        '''
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(digest="ABC", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID"))

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
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(
                task_type = task_type,
                created="2021-06-11T02:37:26.009506Z", file_name='MyInversion.zip', file_size=1000, produced_by="PRODUCER_ID"))

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
        result = self.client.execute(CREATE_QRY,
            variable_values=dict(parent_id=parent_id, child_id=child_id))
        print(result)
        return result['data']['create_task_relation']['thing_relation']

    def create_inversion_solution_nrml(self, upstream_sid):
        """test helper"""
        query = '''
            mutation ($source_solution: ID!, $digest: String!, $file_name: String!, $file_size: Int!, $created: DateTime!) {
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
                inversion_solution_nrml { id, file_name, file_size, md5_digest, post_url, source_solution { id }}
              }
            }'''

        fake_file = fake_file_content()
        variables = dict(source_solution=upstream_sid, file=fake_file, digest=file_digest(fake_file),
            file_name="alineortwo.zip", file_size=file_size(fake_file),
            created = dt.datetime.utcnow().isoformat())
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result

    def create_file(self, filename):
        """test helper"""
        query = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!) {
              create_file(
                    md5_digest:$digest
                    file_name: $file_name
                    file_size: $file_size
                ) {
                    ok
                    file_result { id, file_name, file_size, md5_digest, post_url }
                }
            }
        '''

        fake_file = fake_file_content()
        variables = dict(file=fake_file, digest=file_digest(fake_file),
            file_name="alineortwo.zip", file_size=file_size(fake_file),
            created=dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables )
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
                      archive: $archive_id
                  }
              )
              {
                ok
                config { id, created, source_models { id } }
              }
            }'''

        variables = dict(sources=sources, archive_id=archive_id,
            created = dt.datetime.now(tzutc()).isoformat())
        result = self.client.execute(query, variable_values=variables )
        print(result)
        return result