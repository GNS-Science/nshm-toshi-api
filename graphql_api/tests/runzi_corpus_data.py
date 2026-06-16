"""Vendored snapshot of runzi GraphQL queries.

DO NOT EDIT BY HAND. Regenerate with:

    python spike/strawberry_poc/tools/refresh_runzi_corpus.py

Snapshot source: GNS-Science/nzshm-runzi at 8f29eb7dc5476a1c236822d95df816aeab4c82b6
Extracted from: runzi/automation/toshi_api/
Operations: 18 (placeholder-templated queries dropped)

This vendored copy exists to keep POC's CI gate honest while runzi
catches up on owning client-side schema validation itself. See
runzi#308 for the long-term plan.
"""

OPERATIONS = [
    (
        'runzi/automation/toshi_api/aggregate_inversion_solution.py::query get_sol_tables ($solution_id: ID!) {',
        """\
query get_sol_tables ($solution_id: ID!) {
            node(id:$solution_id) {
              ... on InversionSolution {
                tables {
                  source_solution
                  created
                  produced_by_id
                  table_type
                  identity
                  table_id
                }
              }
            }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/general_task.py::query one_general ($id:ID!)  {',
        """\
query one_general ($id:ID!)  {
              node(id: $id) {
                __typename
                ... on GeneralTask {
                  id
                  title
                  description
                  created
                  children {
                    #total_count
                    edges {
                      node {
                        child {
                          __typename
                          ... on Node {
                            id
                          }
                          ... on RuptureGenerationTask {
                            created
                            state
                            result
                            arguments {k v}
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/general_task.py::mutation create_gt ($created:DateTime!, $agent_name:String!,',
        """\
mutation create_gt ($created:DateTime!, $agent_name:String!, $title:String!, $description:String!,
              $argument_lists: [KeyValueListPairInput]!, $subtask_type:TaskSubType!, $subtask_count:Int!,
              $model_type: ModelType!, $meta: [KeyValuePairInput]!) {
              create_general_task (
                input: {
                  created: $created
                  agent_name: $agent_name
                  title: $title
                  description: $description
                  argument_lists: $argument_lists
                  subtask_type: $subtask_type
                  subtask_count:$subtask_count
                  model_type: $model_type
                  meta:$meta
                })
                {
                  general_task {
                    id
                  }
                }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/general_task.py::mutation update_subtask_count (',
        """\
mutation update_subtask_count (
              $task_id:ID!
              $subtask_count:Int!
            ){
              update_general_task(input:{
                task_id:$task_id
                subtask_count:$subtask_count
              }) {
                ok
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/inversion_solution.py::mutation ($input: AppendInversionSolutionTablesInput!) {',
        """\
mutation ($input: AppendInversionSolutionTablesInput!) {
              append_inversion_solution_tables(input: $input)
               {
               ok
               inversion_solution {
                  id,
                  tables {
                    identity
                    table_id
                    table {
                     id
                    }
                  }
                }
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/inversion_solution.py::query get_sol_tables ($solution_id: ID!) {',
        """\
query get_sol_tables ($solution_id: ID!) {
            node(id:$solution_id) {
              ... on InversionSolution {
                tables {
                  created
                  produced_by_id
                  table_type
                  identity
                  table_id
                }
              }
            }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/openquake_hazard/openquake_hazard_config.py::mutation ($created: DateTime!, $source_models: [ID]!, $archi',
        """\
mutation ($created: DateTime!, $source_models: [ID]!, $archive_id: ID!) {
              create_openquake_hazard_config(
                  input: {
                      created: $created
                      source_models: $source_models
                      template_archive: $archive_id
                  }
              )
              {
                ok
                config { id, created, source_models {
                  ... on Node { id } }
                }
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/openquake_hazard/openquake_hazard_config.py::mutation create_file_relation(',
        """\
mutation create_file_relation(
            $thing_id:ID!
            $file_id:ID!
            $role:FileRole!) {
              create_file_relation(
                file_id:$file_id
                thing_id:$thing_id
                role:$role
              )
            {
              ok
            }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/openquake_hazard/openquake_hazard_config.py::query get_hazard_config ($config_id: ID!) {',
        """\
query get_hazard_config ($config_id: ID!) {
          node(id:$config_id) {
            __typename
            ... on OpenquakeHazardConfig{
              created
              source_models { id }
              template_archive {
                id
                file_name
                file_url
                file_size
                md5_digest
                meta {k v}
              }
            }
          }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/scaled_inversion_solution.py::query get_sol_tables ($solution_id: ID!) {',
        """\
query get_sol_tables ($solution_id: ID!) {
            node(id:$solution_id) {
              ... on InversionSolution {
                tables {
                  source_solution
                  created
                  produced_by_id
                  table_type
                  identity
                  table_id
                }
              }
            }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query one_general ($id:ID!)  {',
        """\
query one_general ($id:ID!)  {
              node(id: $id) {
                __typename
                ... on GeneralTask {
                  id
                  title
                  description
                  created
                  #swept_arguments
                  children {
                    #total_count
                    edges {
                      node {
                        child {
                          __typename
                          ... on Node {
                            id
                          }
                          ... on AutomationTaskInterface {
                            created
                            state
                            result
                            arguments {k v}
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::fragment task_files on FileRelationConnection {',
        """\
fragment task_files on FileRelationConnection {
            total_count
            edges {
              node {
                ... on FileRelation {
                  role
                  file {
                    ... on Node {
                      id
                    }
                    ... on FileInterface {
                      file_name
                      file_size
                      meta {k v}
                    }
                  }
                }
              }
            }
          }

          query ($id:ID!) {
              node(id: $id) {
              __typename
              ... on Node {
                id
              }
              ... on AutomationTask {
                files {
                  ...task_files
                }
              }
              ... on RuptureGenerationTask {
                files {
                  ...task_files
                }
              }
            }
          }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query one_rupt ($id:ID!)  {',
        """\
query one_rupt ($id:ID!)  {
              node(id: $id) {
                __typename
                ... on RuptureGenerationTask {
                  id
                  created
                  arguments {k v}
                }
              }
            }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query file ($id:ID!) {',
        """\
query file ($id:ID!) {
                node(id: $id) {
            __typename
            ... on Node {
              id
            }
            ... on FileInterface {
              file_name
              file_size
              meta {k v}
              file_url
            }
          }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query download_file ($id:ID!) {',
        """\
query download_file ($id:ID!) {
                node(id: $id) {
            __typename
            ... on Node {
              id
            }
            ... on FileInterface {
              file_name
              file_size
              file_url
            }
          }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query pred ($id:ID!) {',
        """\
query pred ($id:ID!) {
          node (id: $id) {
            ... on PredecessorsInterface {
              predecessors {
                id, depth
              }
            }
          }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::mutation create_table (',
        """\
mutation create_table (
          $rows: [[String]]!, $object_id: ID!, $table_name: String!, $headers: [String]!,
          $column_types: [RowItemType]!, $created: DateTime!, $table_type: TableType!,
          $dimensions: [KeyValueListPairInput]!
        ) {
          create_table(input: {
            name: $table_name
            created: $created
            table_type: $table_type
            dimensions: $dimensions
            object_id: $object_id
            column_headers: $headers
            column_types: $column_types
            rows: $rows
            })
          {
            table {
              id
            }
          }
        }
""",
    ),
    (
        'runzi/automation/toshi_api/toshi_api.py::query get_table($table_id:ID!) {',
        """\
query get_table($table_id:ID!) {
          node(id: $table_id) {
            ... on Table {
              id
              name
              created
              table_type
              object_id
              column_headers
              column_types
              rows
              dimensions{k v}
            }
          }
        }
""",
    ),
]
