# Changelog

## [0.3.2] - 2025-10-29
### Changed
 - fix index exception caused by ENUM objects
 - search_manager will now raise exceptions on Elasticsearch.index failures  
 - add test mocking for Elasticsearch
 - hack for indexing compressed relations in FileData objects

## [0.3.1] - 2025-10-29

### Changed
 - remove Node interface from ObjectIdentity schema type.
 - replace `elasticsearch` with `elasticsearch7-compatible` for updated urllib3 dependency.
 - update all search_manager init calls, as auth API changed with urllib3 update.
 - update dependencies

## [0.3.0] - 2025-10-22

### Changed
 - migrate to serverless 4
 - python 3.12
 - migrate pyproject.toml to PEP508
 - ensureCI/CD workflows use minimum install footprints

### Added
 - tox audit step

## [0.2.7] - 2025-09-24

### Changed
 - move to yarn2 for node package management
 - updated to shared workflows
 - upgrade serverless components
 - python advisory patches

## [0.2.6] - 2025-08-07

### Changed
 - fix for enum types in list attributes (see issue #252)

## [0.2.5] - 2025-07-21
### Changed
 - Deprecated config and modified_config in OpenquakeHazardSolution and OpenquakeHazardTask
 - OpenquakeHazardTask: add executor field
 - OpenquakeHazardTask: added srm_logic_tree, gmcm_logic_tree, and openquake_config fields


## [0.2.4] - 2024-07-10
### Added
 - new e2e_workflow test package to reproduce end-user workflows
 - fixed casing for new  mfd_table resolver.

## [0.2.3] - 2024-07-10
### Changed
 - InversionSolutionInterface.mfd_table resolver now uses tables
 - InversionSolutionInterface.produced_by_id is removed (was deprecated)


## [0.2.2] - 2024-06-27
### Changed
 - Schema.nodes resolver now handles all InversionSolution types
 - AutomationTask.inversion_solution resolver now handles all InversionSolution types

## [0.2.1] - 2024-06-20

### Changed
 - fix for issue #217 (from graphe library upgrade)
 - improve test coverage with moto libary
 - migrate enum.value fix into base_data

## [0.2.0] - 2024-06-14

### Changed
 - fixed `source_solution` resolvers bug #214 - breaking graphql API change
 - upgraded NPM packages
 - updated flask, flask-cors graphene libraries (major verion update)
 - replace superceded `flask_graphql` import with `graphql_server.flask`
 - elastic search index name is now `toshi_index_mapped`
 - fixed index update method

### Added
 - CHANGELOG.md and .bumpversion.cfg files
 - added QA tools to worklow: `black, isort. tox`
 - new resolvers: `object_identities` and `legacy_object_identities`
 - new resolvers: `about` and `version`

### Removed
 - setup.py
 - many unused imports (with autoflake)