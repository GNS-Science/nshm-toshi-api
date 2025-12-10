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
        subtask_type: OPENQUAKE_HAZARD,
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
def create_at_mutation():
    yield '''
    mutation ($created: DateTime!, $gt_id: ID,  $arguments: [KeyValuePairInput]! ) {
        create_automation_task(input: {
            general_task_id: $gt_id
            task_type: INVERSION
            state: UNDEFINED
            result: UNDEFINED
            created: $created
            duration: 600

            arguments: $arguments

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
