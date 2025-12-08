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
