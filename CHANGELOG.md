# Changelog

## [0.2.0] - 2024-06-14

### Changed
 - upgraded NPM packages
 - updated flask, flask-cors graphene libraries (major verion update)
 - replace superceded `flask_graphql` import with `graphql_server.flask`
 - elasctic search index name is now `toshi_index_mapped`
 - fixed index update method

### Added
 - CHANGELOG.md and .bumpversion.cfg files
 - added QA tools to worklow: `black, isort. tox`
 - new resolvers: `object_identities` and `legacy_object_identities`
 - new resolvers: `about` and `version`

### Removed
 - setup.py
 - many unused imports (with autoflake)