# Changelog

## [0.6.0] - 2026-05-11

### Added
 - **JWT authentication** replacing the single shared `x-api-key` with per-user Cognito JWTs
   - Lambda Authorizer (`auth/authorizer/handler.py`) validates JWTs and legacy API keys
   - Flask middleware (`auth/middleware.py`) enforces `toshi/read` and `toshi/write` scopes
   - Scientist CLI (`auth/toshi_auth.py`) for login, token management, and AWS credentials
   - All Cognito infrastructure provisioned via CloudFormation in `serverless.yml`
 - **Backward compatibility**: legacy `x-api-key` clients continue working via `LEGACY_API_KEY`
   env var (reads `NZSHM22_TOSHI_API_KEY` in CI)
 - **Token flows**: USER_PASSWORD_AUTH for scientists, client credentials for M2M/Runzi
 - **IAM roles** for Runzi workloads via Cognito Identity Pool (`runzi-local/batch/admin`)
 - 38 unit tests across authorizer handler and middleware mutation detection

### Changed
 - GraphQL events use Lambda Authorizer instead of `private: true` API key plan
 - Mutation detection uses `graphql-core` AST parser (was regex — had false positives)
 - Lambda package reduced from 329MB to 120MB by excluding dev artifacts
 - Middleware is no-op when `TESTING=1` or `SLS_OFFLINE=1` — local dev unaffected
 - Migrated from Poetry to uv; replaced flake8/black/isort with ruff
 - CI deploy workflow uses GitHub environments (`AWS_TEST`/`AWS_PROD`) for per-stage secrets

### Security
 - Test user credentials and client secrets kept in gitignored local files only
 - Authorizer only accepts access tokens (id tokens rejected)

### Future (Phase 2)
 - Entra ID (Azure AD) OIDC federation for GNS corporate SSO
 - Client library (`nshm-toshi-client`) migration to Bearer tokens

## [0.5.2] - 2025-12-15

### Changed
 - added `created` attribute to FileInterface schema.
 - made `required` explicit for CreateFile input fields.
 - use CreateFile input types in `create_rupture_set`.
 - corrected RuptureSet to use `meta` instead of `arguments`.
 - corrected type of `RuptureSet.produced_by` to `RuptureGenerationTask`.

## [0.5.1] - 2025-12-12

### Added
 - add required `task_type` attribute to `OpenquakeHazardSolution` (breaking change).
 - new `RuptureSet` subclasses File with specific attributes.
 - new ENV variables:
    - `DB_READ_ONLY` for safe testing agains LIVE backends, default = False.
    - `CLOUDWATCH_ENABLED` for disabling cloud metrics, default = True.
    - `MIGRATE_FILE_TO_RUPTSET` for `RuptureSet` class migrations, default = False.
 - new resolvers for FileData objects:`post_url_v2` and `post_data_v2`
    to make upload testing possible, and to better align with boto3 API. 
    NB `nshm-toshi-client`should migrate to these, but not required immediately.

### Changed
 - for `AutomationTask` the mutation task_type = Required is now enforced.
   - make `task_type` consistent acrosss `AutomationTask` and subclasses.
   - udpate `AutomationTaskInterface` schema type

## [0.4.0] - 2025-12-02

### Added
 - setup python-dotenv for .env file based configuration
 - new package tests/swept_arguments added

### Changed
 - AutomationTask create mutation now performs argument validation when a general_task_id is supplied
 - libary updates - moto 5 API change affects many tests
 - serverless-python-requirements is no longer a plugin


## [0.3.2] - 2025-11-03
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