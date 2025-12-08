import datetime

import pytest


@pytest.fixture(scope='session')
def create_gt_mutation():
    yield '''
    mutation new_gt (
        $created: DateTime!,
        $argument_lists: [KeyValueListPairInput]!
        ) {
      create_general_task(input:{
        created: $created
        title: "TEST Build opensha rupture set Coulomb #1"
        description:"Using "
        agent_name:"chrisbc"
        subtask_type: RUPTURE_SET
        model_type: COMPOSITE
        argument_lists: $argument_lists
      })
      {
        general_task{
          id
          subtask_type
          model_type
          argument_lists {k v}
          swept_arguments 
        }
      }
    }
'''


@pytest.fixture(scope='session')
def create_rs_mutation():
    yield '''
    mutation ($created: DateTime!, $gt_id: ID, $arguments: [KeyValuePairInput]!) {
        create_rupture_generation_task(input: {
            state: UNDEFINED
            result: UNDEFINED        
            created: $created
            general_task_id: $gt_id
            arguments: $arguments

            environment: [
                { k:"gitref_opensha_ucerf3" v: "ABC"}
                { k:"gitref_opensha_commons" v: "ABC"}
                { k:"gitref_opensha_core" v: "ABC"}
                { k:"nshm_nz_opensha" v: "ABC"}
                { k:"host" v:"tryharder-ubuntu"}
                { k:"JAVA" v:"-Xmx24G"  }
            ]

            ##EXTRA_INPUT##

        })
        {
            task_result {
                id
                created
                duration
                arguments {k v}
                general_task_id
            }
        }
    }
'''


@pytest.fixture()
def rupture_generation_task(graphql_client, create_gt_mutation, create_rs_mutation):

    # create the GT to be referenced in the AT
    gt1 = graphql_client.execute(
        create_gt_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), argument_lists=[dict(k="swept_arg", v=["A", "B"])]
        ),
    )
    print(gt1)
    gt_id = gt1['data']['create_general_task']['general_task']['id']

    # Now create the Rupture Generation task
    executed = graphql_client.execute(
        create_rs_mutation,
        variable_values=dict(
            created=datetime.datetime.now(datetime.UTC), gt_id=gt_id, arguments=dict(k="swept_arg", v="A")
        ),
    )
    task_result = executed['data']['create_rupture_generation_task']['task_result']
    yield task_result


@pytest.fixture()
def create_rupture_set_mutation():
    yield """
        mutation (
            $md5_digest: String!, 
            $file_name: String!, 
            $file_size: BigInt!, 
            $produced_by: ID!
            $arguments: [KeyValuePairInput],
            $metrics: [KeyValuePairInput],
            $created: DateTime!
            $fault_models: [String]!  
        ) {
              create_rupture_set(
                input: {
                  md5_digest: $md5_digest
                  file_name: $file_name
                  file_size: $file_size
                  produced_by: $produced_by
                  arguments: $arguments
                  metrics: $metrics
                  created: $created
                  fault_models: $fault_models
                  }
              ) {
              rupture_set { 
                id
                file_name
                file_size
                md5_digest
                created
                fault_models
                produced_by { id __typename, general_task_id}
                arguments { k v }
                metrics { k v }
                }
              }
            }
    """
